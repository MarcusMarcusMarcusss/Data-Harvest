function copyToClipboard(id, button) {
    const fullText = document.getElementById(id).textContent;
    navigator.clipboard.writeText(fullText).then(() => {
        const originalText = button.textContent;
        button.textContent = "Copied";
        setTimeout(() => {
            button.textContent = originalText;
        }, 500);
    });
}

document.querySelectorAll("span[id^='link']").forEach(span => {
    const full = span.textContent.trim();
    const parts = full.split("/");
    if (parts.length > 15) {
        span.textContent = parts.slice(0, 15).join("/") + "...";
    }
});

async function downloadPage() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        unit: 'pt',
        format: 'a4',
        orientation: 'portrait'
    });

    const now = new Date();
    const iso = now.toISOString();
    const timestamp = iso.substring(0, 19).replace('T', ' ').replace(/:/g, '-');
    const filename = `Course Inspector - ${timestamp}.pdf`;

    doc.text("Course Inspector - Extracted URLs", 40, 40);
    let currentY = 60;

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
                3: { cellWidth: 200 } 
            },
            didDrawPage: function (data) {
                currentY = data.cursor.y + 30;
            }
        });
    });

    doc.save(filename);
}