import base64
from odoo import models, fields, api
import barcode
from barcode.writer import ImageWriter
import io
import random
import string

class ShipmentOrder(models.Model):
    _name = 'shipment.order.payment'
    _description = 'Shipment Order Payment'

    # Fields for sender and receiver information
    sender_account_number = fields.Char(string='Sender Account Number')
    invoice_to_receiver = fields.Char(string='Invoice to Receiver')
    lead_id = fields.Many2one('crm.lead', 'Lead ID')
    barcode = fields.Char(string="Barcode", copy=False, readonly=True)
    barcode_image = fields.Binary(string="Barcode Image")
    # Fields for sender and receiver address
    sender_company_name = fields.Char(string='Sender Company Name')
    sender_address = fields.Char(string='Sender Address')
    sender_city = fields.Char(string='Sender City')
    sender_post_zip_code = fields.Char(string='Sender Post/Zip Code')
    sender_province = fields.Char(string='Sender Province')
    sender_country = fields.Char(string='Sender Country')
    sender_contact_name = fields.Char(string='Sender Contact Name')
    sender_tel = fields.Char(string='Sender Tel')

    receiver_company_name = fields.Char(string='Receiver Company Name')
    receiver_address = fields.Char(string='Receiver Address')
    receiver_city = fields.Char(string='Receiver City')
    receiver_post_zip_code = fields.Char(string='Receiver Post/Zip Code')
    receiver_province = fields.Char(string='Receiver Province')
    receiver_country = fields.Char(string='Receiver Country')
    receiver_contact_name = fields.Char(string='Receiver Contact Name')
    receiver_tel = fields.Char(string='Receiver Tel')

    # Dangerous Goods
    dangerous_goods_yes = fields.Boolean( string="YES")
    dangerous_goods_no = fields.Boolean( string="NO")

    # Fragile Goods
    fragile_goods_yes = fields.Boolean(string="YES")
    fragile_goods_no = fields.Boolean(string="NO")

    dangerous_goods = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Does this consignment contain any dangerous goods?")

    # Fragile Goods
    fragile_goods = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Does this consignment contain any fragile goods?")

    # Signature and Date
    sender_signature = fields.Char(string='Sender Signature')
    received_by_jet_express = fields.Char(string='Received By Jet Express')
    sender_date = fields.Date(string='Sender Date')
    jet_express_date = fields.Date(string='Jet Express Date')

    # Services
    services_10_00_express_doc = fields.Boolean(string='10.00 Express Document')
    services_10_00_express_non_doc = fields.Boolean(string='10.00 Express Non Document')
    services_10_00_express_same_day = fields.Boolean(string='10.00 Express Same Day')

    services_12_00_express_doc = fields.Boolean(string='12.00 Express Document')
    services_12_00_express_non_doc = fields.Boolean(string='12.00 Express Non Document')
    services_12_00_express_same_day = fields.Boolean(string='12.00 Express Same Day')

    services_express_doc = fields.Boolean(string='Express Document')
    services_express_non_doc = fields.Boolean(string='Express Non Document')
    services_express_same_day = fields.Boolean(string='Express Same Day')

    # Goods Description
    goods_description_1 = fields.Text(string='Goods Description 1')
    number_of_items_1 = fields.Integer(string='Number of Items 1')
    weight_kg_1 = fields.Float(string='Weight (Kg) 1')
    weight_g_1 = fields.Float(string='Weight (Grams) 1')
    dimensions_1 = fields.Char(string='Dimensions (cm) 1')

    goods_description_2 = fields.Text(string='Goods Description 2')
    number_of_items_2 = fields.Integer(string='Number of Items 2')
    weight_kg_2 = fields.Float(string='Weight (Kg) 2')
    weight_g_2 = fields.Float(string='Weight (Grams) 2')
    dimensions_2 = fields.Char(string='Dimensions (cm) 2')

    goods_description_3 = fields.Text(string='Goods Description 3')
    number_of_items_3 = fields.Integer(string='Number of Items 3')
    weight_kg_3 = fields.Float(string='Weight (Kg) 3')
    weight_g_3 = fields.Float(string='Weight (Grams) 3')
    dimensions_3 = fields.Char(string='Dimensions (cm) 3')


    # Additional information
    special_delivery_instruction = fields.Text(string='Special Delivery Instruction')
    shipment_disclaimer = fields.Text(string='Shipment Disclaimer')
    compensation_policy = fields.Text(string='Compensation Policy')
    company_id = fields.Many2one('res.company', required=False, readonly=False, default=lambda self: self.env.company)

    # Computed Fields for Summation
    total_number_of_items = fields.Integer(string='Total Number of Items', compute='_compute_total_items', store=True)
    total_weight_kg = fields.Float(string='Total Weight (Kg)', compute='_compute_total_weight_kg', store=True)
    total_weight_g = fields.Float(string='Total Weight (Grams)', compute='_compute_total_weight_g', store=True)

    @api.depends('number_of_items_1', 'number_of_items_2',)
    def _compute_total_items(self):
        for record in self:
            record.total_number_of_items = (
                    record.number_of_items_1 +
                    record.number_of_items_2
            )

    @api.depends('weight_kg_1', 'weight_kg_2', )
    def _compute_total_weight_kg(self):
        for record in self:
            record.total_weight_kg = (
                    record.weight_kg_1 +
                    record.weight_kg_2
            )

    @api.depends('weight_g_1', 'weight_g_2',)
    def _compute_total_weight_g(self):
        for record in self:
            record.total_weight_g = (
                    record.weight_g_1 +
                    record.weight_g_2
            )

    def action_generate_barcode(self):
        """Generate barcode and barcode image"""
        for record in self:
            if not record.barcode:
                record.barcode = self._generate_barcode()
            record._generate_barcode_image()

    def _generate_barcode(self):
        """Generate a unique barcode"""
        barcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        return barcode

    def _generate_barcode_image(self):
        """Generate a barcode image and store it in the barcode_image field"""
        for record in self:
            if record.barcode:
                ean = barcode.get('code128', record.barcode, writer=ImageWriter())
                buffer = io.BytesIO()
                ean.write(buffer)
                record.barcode_image = base64.b64encode(buffer.getvalue())
                buffer.close()

def _generate_barcode_image(self):
    """Generate a barcode image and store it in the barcode_image field"""
    for record in self:
        if record.barcode:
            # Generate the barcode in memory using BytesIO
            ean = barcode.get('code128', record.barcode, writer=ImageWriter())
            buffer = io.BytesIO()
            ean.write(buffer)
            record.barcode_image = base64.b64encode(buffer.getvalue())
            buffer.close()