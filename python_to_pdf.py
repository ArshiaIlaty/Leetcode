from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

with open("your_script.py", "r") as f:
    for line in f:
        pdf.cell(200, 10, txt=line, ln=True)

pdf.output("output.pdf")
