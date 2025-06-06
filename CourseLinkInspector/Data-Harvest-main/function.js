document.addEventListener('DOMContentLoaded', () => {
    // Search courses
    document.getElementById('course-search').addEventListener('input', function () {
        const term = this.value.toLowerCase();
        const labels = document.querySelectorAll('#course-list label');
        labels.forEach(label => {
            const text = label.textContent.toLowerCase();
            label.style.display = text.includes(term) ? '' : 'none';
        });
    });

    // Search coordinators
    document.getElementById('coordinator-search').addEventListener('input', function () {
        const term = this.value.toLowerCase();
        const labels = document.querySelectorAll('#coordinator-list label');
        labels.forEach(label => {
            const text = label.textContent.toLowerCase();
            label.style.display = text.includes(term) ? '' : 'none';
        });
    });
});