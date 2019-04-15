# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import base64, datetime, pdf2image, StringIO


class AccountInvoice(models.Model):
    _inherit = ["account.invoice"]

    free_text = fields.Html(string='Invoice body as Free Text')

    # TODO: check if this is needed?
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent
        """
        self.ensure_one()
        if self.type == 'out_refund':
            for line in self.invoice_line_ids:
                if not line.so_line_id:
                    line.so_line_id = line.origin_line_ids.sale_line_ids.id
        return super(AccountInvoice, self).invoice_print()

    def _get_refund_common_fields(self):
        res = super(AccountInvoice, self)._get_refund_common_fields()
        if self.ad:
            res = res+['published_customer']
        return res

    def _get_refund_copy_fields(self):
        copy_fields = ['company_id', 'user_id', 'fiscal_position_id', 'free_text']
        return self._get_refund_common_fields() + self._get_refund_prepare_fields() + copy_fields

    @api.model
    def _refund_cleanup_lines(self, lines):
        if self.env.context.get('mode') == 'modify':
            result = super(AccountInvoice, self).with_context(mode=False)._refund_cleanup_lines(lines)
            for i in xrange(0, len(lines)):
                for name, field in lines[i]._fields.iteritems():
                    if name == 'so_line_id' and not lines[i][name]:
                        result[i][2][name] = lines[i]['sale_line_ids'].id
                        lines[i][name] = lines[i]['sale_line_ids'].id
                    if name == 'sale_line_ids':
                        result[i][2][name] = [(6, 0, lines[i][name].ids)]
                        lines[i][name] = False
                    if name == 'sale_order_id':
                        result[i][2].pop(name, None)
                    if name == 'ad':
                        result[i][2].pop(name, None)
        else:
            result = super(AccountInvoice, self)._refund_cleanup_lines(lines)
            for i in xrange(0, len(lines)):
                for name, field in lines[i]._fields.iteritems():
                    if name == 'so_line_id' and not lines[i][name]:
                        result[i][2][name] = lines[i]['sale_line_ids'].id
                        lines[i][name] = lines[i]['sale_line_ids'].id
                    if name == 'sale_order_id':
                        result[i][2].pop(name, None)
                    if name == 'ad':
                        result[i][2].pop(name, None)
        return result


    @api.model
    def has_attachment(self):
        attachments = self.env['ir.attachment'].search([('res_model','=','account.invoice'), 
                                                        ('res_id','=',self.id),              
                                                        ('mimetype','=','application/pdf'),  
                                                        ('res_name','like',self.number)])
        if len(attachments) == 1 :
            return True
        else:
            return False

    @api.model
    def invoice_attachment_as_image(self, scale):
        attachments = self.env['ir.attachment'].search([('res_model','=','account.invoice'), 
                                                        ('res_id','=',self.id),              
                                                        ('mimetype','=','application/pdf'),  
                                                        ('res_name','like',self.number)])
        if len(attachments) == 1 :
            data    = attachments[0].datas
            b64data = base64.b64decode(data)
            image   = pdf2image.convert_from_bytes(b64data) #is PIL format
            size    = int(image[0].width*scale) , int(image[0].height*scale)
            #image[0]= image[0].resize(size) #resizing by wkhtmltopdf gives better quality
            embed_string = ""
            for page in image :
                buf     = StringIO.StringIO()
                page.save(buf, format= 'JPEG')
                jpeg    = buf.getvalue()
                buf.close()
                b64jpeg = base64.b64encode(jpeg)
                embed_string += '<img src="data:image/jpeg;base64,'+b64jpeg+'" width="'+str(size[0])+'px" height="'+str(size[1])+'px"/>'
            return embed_string
        else :
            return "n.a."



class AccountInvoiceLine(models.Model):
    _inherit = ["account.invoice.line"]


    @api.model
    def create(self, vals):
        ctx = self.env.context.copy()
        line_obj = super(AccountInvoiceLine, self).create(vals)
        if 'active_model' in ctx:
            if ctx.get('active_model') in ('sale.order','sale.order.line'):
                for sale_line_obj in line_obj.sale_line_ids:
                    description = False
                    if sale_line_obj.order_id.operating_unit_id.use_bduprint and line_obj.product_id == sale_line_obj.product_id and sale_line_obj.product_id.product_tmpl_id.invoice_description:
                        description = sale_line_obj.name
                    if description:
                        line_obj.write({'name':description})
        return line_obj



