from flask import Flask, render_template_string, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import qrcode

app = Flask(__name__)

HTML_FORM = '''
<!doctype html>
<title>Letterhead Generator</title>
<h2>Letterhead PDF Generator</h2>
<form method=post enctype=multipart/form-data>
  Company Name: <input name=companyName><br>
  Manager Name: <input name=managerName><br>
  Bank Name: <input name=bank_name><br>
  Account Number: <input name=account_number><br>
  Employee Name: <input name=employeeName><br>
  Employee ID: <input name=employeeId><br>
  From Date: <input type=date name=date_1><br>
  To Date: <input type=date name=date_2><br>
  Company Stamp: <input type=file name=companyStamp><br>
  <input type=submit value=Generate>
</form>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get form data
        companyName = request.form['companyName']
        managerName = request.form['managerName']
        bank_name = request.form['bank_name']
        account_number = request.form['account_number']
        employeeName = request.form['employeeName']
        employeeId = request.form['employeeId']
        date_1 = request.form['date_1']
        date_2 = request.form['date_2']

        # Handle images
        companyStamp = request.files['companyStamp']

        # Generate barcode image
        barcode_io = BytesIO()
        barcode = Code128(account_number, writer=ImageWriter())
        barcode.write(barcode_io)
        barcode_io.seek(0)
        barcode_img = Image.open(barcode_io)

        # Prepare PDF
        pdf_io = BytesIO()
        c = canvas.Canvas(pdf_io, pagesize=A4)
        width, height = A4

        # Letterhead
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height-50, companyName)
        c.setFont("Helvetica", 12)
        c.drawString(50, height-80, "Address Line 1")
        c.drawString(50, height-100, "Address Line 2")

        # Custom details
        c.drawString(50, height-140, f"Manager: {managerName}")
        c.drawString(50, height-160, f"Employee: {employeeName}")
        c.drawString(50, height-180, f"Employee ID: {employeeId}")

        # Description
        desc = f"""Dear Sir/Madam,

I, {managerName} holding account number {account_number} in {bank_name}, hereby allow {employeeName} to act on my behalf for the purpose of managing my account, performing transactions,
and handling any issues related to my account. This Authorization will be valid from {date_1} to {date_2}.

{employeeName} bearing ID number {employeeId} is hereby granted the following privileges for my account:
1. Withdrawal and deposit of funds.
2. Check issuance and clearance.
3. Requesting account statement and balance inquiry.
4. Demand Draft can be requested.

Kindly provide {employeeName} with access to all necessary account information and grant permission to perform the above mentioned transactions during the specified period. Any transactions and requests made by {employeeName} within the scope of this authorization should be treated as legitimate and processed accordingly.

Thank you for your cooperation and understanding.
"""
        text = c.beginText(50, height-220)
        text.setFont("Helvetica", 11)
        for line in desc.splitlines():
            text.textLine(line)
        c.drawText(text)

        # Add barcode
        c.drawInlineImage(barcode_img, 50, 100, width=200, height=50)

        # If a PDF is uploaded, generate a QR code for its link and embed it
        uploaded_pdf = request.files.get('customQR')
        if uploaded_pdf and uploaded_pdf.filename:
            # Save the uploaded PDF temporarily
            pdf_path = f"/tmp/{uploaded_pdf.filename}"
            uploaded_pdf.save(pdf_path)
            # For demo: use a local file path as the QR content (in real use, upload to a server and use a public URL)
            qr_content = f"file://{pdf_path}"
            qr_io = BytesIO()
            qr_img = qrcode.make(qr_content)
            qr_img.save(qr_io, format='PNG')
            qr_io.seek(0)
            c.drawInlineImage(Image.open(qr_io), 400, 100, width=80, height=80)

        # Add images if provided
        y_img = 300
        if companyStamp and companyStamp.filename:
            img = Image.open(companyStamp)
            c.drawInlineImage(img, 300, y_img, width=80, height=80)

        c.save()
        pdf_io.seek(0)
        return send_file(pdf_io, as_attachment=True, download_name='letterhead.pdf', mimetype='application/pdf')

    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    app.run(debug=True)