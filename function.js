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

document.querySelectorAll('table').forEach((table) => {
    table.querySelectorAll('th.sortable').forEach((header, columnIndex) => {
        let ascending = true;

        header.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                const cellA = a.children[columnIndex].textContent.trim().toLowerCase();
                const cellB = b.children[columnIndex].textContent.trim().toLowerCase();
                if (columnIndex === 0 && !isNaN(Date.parse(cellA)) && !isNaN(Date.parse(cellB))) {
                    return ascending ? new Date(cellA) - new Date(cellB) : new Date(cellB) - new Date(cellA);
                }
                return ascending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            });

            rows.forEach(row => tbody.appendChild(row));
            ascending = !ascending;
        });
    });
});

async function downloadPage() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
        unit: 'pt',
        format: 'a4',
        orientation: 'landscape'
    });

    const now = new Date();
    const iso = now.toISOString();
    const timestamp = iso.substring(0, 19).replace('T', ' ').replace(/:/g, '-');
    const filename = `Course Inspector - ${timestamp}.pdf`;
    const coordinatorName = "<?php echo htmlspecialchars($coordinator['CoordinatorName']); ?>";
    const coordinatorEmail = "<?php echo htmlspecialchars($coordinator['CoordinatorEmail']); ?>";

    doc.text("Course Inspector - Extracted URLs", 40, 40);
    doc.text(`Unit Coordinator: ${coordinatorName}`, 40, 60);
    doc.text(`Email: ${coordinatorEmail}`, 40, 80);
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
            styles: { fontSize: 10, cellPadding: 4 },
            columnStyles: { 3: { cellWidth: 170 } },
            didDrawPage: function (data) {
                currentY = data.cursor.y + 30;
            }
        });
    });

    doc.save(filename);
}

