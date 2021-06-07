import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DJBCNofasMasukV2(models.Model):
    _name = 'djbc.nofas_masuk_v2'
    _description = 'DJBC Laporan Pemasukan'
    _rec_name = 'no_dok'

    jenis_dok = fields.Char(string='Jenis Dokumen')
    no_aju = fields.Char(string='Nomor Aju')
    tgl_aju=fields.Date(string='Tgl Aju')
    no_dok=fields.Char (string='Nomor Pendaftaran')
    # no_dok  = fields.Many2one(comodel_name="djbc.docs", string="Nomor Pendaftaran", required=False, )
    tgl_dok=fields.Date(string='Tgl Pendaftaran')
    # no_penerimaan = fields.Many2one(comodel_name="stock.picking", string="Nomor Penerimaan", required=False, )
    no_penerimaan =fields.Char (string='Nomor Penerimaan')
    tgl_penerimaan=fields.Date(string='Tgl Penerimaan')
    no_bl = fields.Char(string='Nomor B/L')
    tgl_bl = fields.Date(string='Tgl B/L')
    no_cont = fields.Char(string='Nomor Container')
    # no_penerimaan=fields.Char(string='Nomor Penerimaan')
    pengirim = fields.Char(string='Pengirim Barang')
    pemilik = fields.Char(string='Pemilik Barang')
    hs_code = fields.Char(string='HS Code')
    kode_barang=fields.Char(string='Kode Barang')
    nama_barang=fields.Char(string='Nama Barang')
    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot No", required=False, )
    jumlah = fields.Float(string='Jumlah')
    satuan = fields.Char(string='Satuan')
    jumlah_kemasan = fields.Float(string='Jumlah Kemasan')
    satuan_kemasan = fields.Char(string='Satuan Kemasan')
    nilai = fields.Float(string='Nilai')
    currency = fields.Char(string='Currency')
    location = 	fields.Char(string='Location')
    warehouse = fields.Char(string='Warehouse')
    alm_wh = fields.Char(string='Alamat Warehouse')
    kota_wh = fields.Char(string='Kota')
    # qty_sisa=fields.Float(string='Sisa')

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
        DROP FUNCTION IF EXISTS djbc_nofas_masuk_v2(DATE, DATE);
        CREATE OR REPLACE FUNCTION djbc_nofas_masuk_v2(date_start DATE, date_end DATE)
RETURNS VOID AS $BODY$
DECLARE

	csr cursor for
		SELECT spp.code,spp.no_dok,spp.tgl_dok,s.reference,s.date,spp.partner,pp.dc1,pp.name AS Barang,s.product_uom_qty,uom.name
        --,s.remaining_qty,s.remaining_value
        ,inv.price_subtotal,al.price_subtotal AS sub,s.invoice_state,
        (case
                    when inv.price_subtotal is not null
                        then inv.name
                    when al.price_subtotal is not null
                        then cur.name
                    else null
                    end) as currency,
                    (case
                    when inv.price_subtotal is not null
                        then inv.price_subtotal
                    when al.price_subtotal is not null
                        then al.price_subtotal
                    else 0.0
                    end) as nilai
        FROM stock_move s

        LEFT JOIN purchase_order_line al ON s.purchase_line_id=al.id
        LEFT JOIN res_currency cur ON al.currency_id=cur.id


        LEFT JOIN (SELECT rel.move_id,al.id,al.price_subtotal,cur.name FROM stock_move_invoice_line_rel rel
                    LEFT JOIN account_invoice_line al ON rel.invoice_line_id=al.id
                    LEFT JOIN res_currency cur ON al.currency_id=cur.id) inv ON s.id=inv.move_id

        LEFT JOIN
        (SELECT ppp.id,pt.name,pt.default_code AS dc1,ppp.default_code AS dc2 FROM product_product ppp LEFT JOIN product_template pt ON ppp.product_tmpl_id=pt.id)
        pp ON s.product_id=pp.id
        LEFT JOIN uom_uom uom ON s.product_uom=uom.id
        LEFT JOIN
            (SELECT sp.id ,sp.name,dok.no_dok,dok.code,dok.tgl_dok,slb.name AS Asal,sl.name AS Tujuan,rp.name AS partner,sp.origin,ai.amount_total as invoice
            FROM stock_picking sp LEFT JOIN stock_location slb ON sp.location_id=slb.id
            LEFT JOIN stock_location sl ON sp.location_dest_id=sl.id
            LEFT JOIN res_partner rp ON sp.partner_id=rp.id
            LEFT JOIN account_invoice ai ON sp.name=ai.origin
            LEFT JOIN (SELECT dok1.id,dok1.no_dok,dok1.tgl_dok,dok2.code FROM djbc_docs dok1 LEFT JOIN djbc_doctype dok2 ON dok1.jenis_dok=dok2.id) dok ON sp.docs_id=dok.id) spp ON s.picking_id=spp.id

        WHERE s.picking_id IN
        (SELECT sp.id --,sp.name,dok.no_dok,slb.name AS Asal,sl.name AS Tujuan
        FROM stock_picking sp
        LEFT JOIN stock_location slb ON sp.location_id=slb.id
        LEFT JOIN stock_location sl ON sp.location_dest_id=sl.id
        LEFT JOIN djbc_docs dok ON sp.docs_id=dok.id
        WHERE sp.docs_id is not NULL AND sl.name='Stock' AND sp.state='done')
		and spp.tgl_dok >= date_start and spp.tgl_dok<=date_end
		order by spp.tgl_dok;

	v_wh text;

BEGIN
	delete from djbc_nofas_masuk_v2;
	-- v_wh='WH/Stock';

	for rec in csr loop
		insert into djbc_nofas_masuk_v2 (no_dok, tgl_dok,jenis_dok,no_penerimaan, tgl_penerimaan, pengirim, kode_barang,
			nama_barang, jumlah, satuan, nilai, currency, warehouse
            --, lot_id, no_bl, tgl_bl, no_aju, tgl_aju, no_cont,
			--jumlah_kemasan, satuan_kemasan, hs_code, pemilik, location, alm_wh, kota_wh
            )
			values (rec.no_dok,rec.tgl_dok, rec.code, rec.reference,rec.date,
				rec.partner,rec.dc1,rec.name,  rec.product_uom_qty,rec.name,
				rec.nilai, rec.currency, 'WH'
                --, rec.lot_id, rec.no_bl, rec.tgl_bl,
				--rec.no_aju, rec.tgl_aju, rec.no_cont, rec.jumlah_kemasan, rec.satuan_kemasan, rec.hs_code,
				--rec.pemilik, rec.location, rec.alm_wh, rec.kota_wh
                ) ;
		-- update stock_move set djbc_masuk_flag=TRUE where id=rec.id;
	end loop;

END;

$BODY$
LANGUAGE plpgsql;
        """)

    # def get_nopen(self):
    #    _logger.info("get_nopen functions...")
    #    for line_id in self.masuk_lines_ids:
    #        _logger.info(line_id.name)
    #        sp_id = self.env['stock.picking'].search([('name','=',line_id.name)])
    #        dok_bc = sp_id.docs_id.read(['no_dok','tgl_dok','jenis_dok'])
    #        if not dok_bc:
    #            _logger.info('dok_bc is empty')
    #        else:
    #            _logger.info(dok_bc[0]['no_dok'])
    #            line_id.write({'no_dok':dok_bc[0]['no_dok'],'tgl_dok':dok_bc[0]['tgl_dok'],'jenis_dok':dok_bc[0]['jenis_dok']})

    # def call_djbc_nofas_masuk(self):
    #    cr = self.env.cr
    #    cr.execute("select djbc_nofas_masuk()")
    #    return {
    #        'name': 'Laporan Pemasukan',
    #        'domain': [],
    #        'view_type': 'form',
    #        'res_model': 'djbc.nofas_masuk',
    #        'view_id': False,
    #        'view_mode': 'tree,form',
    #        'type': 'ir.actions.act_window',
    #    }
