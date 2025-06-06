
function downloadPage() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        unit: 'pt',
        format: 'a4',
        orientation: 'landscape'
    });

    const now = new Date();
    const iso = now.toISOString();
    const timestamp = iso.substring(0, 19).replace('T', ' ').replace(/:/g, '-');
    const filename = `${document.title} - ${timestamp}.pdf`;

    // Get the coordinator info from the visible page content
    const infoText = document.getElementById("coordinator-info")?.innerText || "";

    doc.setFontSize(16);
    doc.text(document.title, 40, 40); // Use page title dynamically

    doc.setFontSize(12);
    doc.text(infoText, 40, 60);

    let currentY = 80;

    const tables = document.querySelectorAll("table");
    tables.forEach((table, index) => {
        const headers = [];
        const body = [];

        const ths = table.querySelectorAll("thead tr th");
        ths.forEach(th => headers.push(th.textContent.trim()));

        const trs = table.querySelectorAll("tbody tr");
        trs.forEach(tr => {
            const row = [];
            const tds = tr.querySelectorAll("td");
            tds.forEach(td => {
                const span = td.querySelector("span");
                row.push(span ? span.textContent.trim() : td.textContent.trim());
            });
            body.push(row);
        });

        doc.autoTable({
            head: [headers],
            body: body,
            startY: currentY,
            margin: { left: 40, right: 40 },
            styles: { fontSize: 9, cellPadding: 4 },
            columnStyles: {
                0: { cellWidth: 100 },
                1: { cellWidth: 70 },  
                2: { cellWidth: 320 },
                3: { cellWidth: 80 }, 
                4: { cellWidth: 210 }, 
            },
            didDrawPage: function (data) {
                currentY = data.cursor.y + 30;
            }
        });
    });

    doc.save(filename);
}

