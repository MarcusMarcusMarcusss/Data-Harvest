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

// Trim long link display
document.querySelectorAll("span[id^='link']").forEach(span => {
    const full = span.textContent.trim();
    const parts = full.split("/");
    if (parts.length > 15) {
        span.textContent = parts.slice(0, 15).join("/") + "...";
    }
});

function downloadPage() {
    const now = new Date();
    const iso = now.toISOString();
    const timestamp = iso.substring(0, 19).replace('T', ' ').replace(/:/g, '-');
    const filename = `Course Inspector - ${timestamp}.pdf`;

    const button = document.getElementById('downloadBtn');
    button.style.display = 'none';

    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.style.display = 'none';
    });

    const element = document.body.cloneNode(true);

    html2pdf().set({
        margin: 0.5,
        filename: filename,
        image: { type: 'jpeg'},
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    }).from(element).save().then(() => {
        button.style.display = 'inline-block';

        copyButtons.forEach(button => {
            button.style.display = 'inline-block';
        });
    });
    
}