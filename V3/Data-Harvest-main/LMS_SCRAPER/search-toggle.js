document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('table-search-input');
    let currentSearchVisible = false;
    const sortDirections = {};

    // Toggle search input on header text click
    document.querySelectorAll('.header-text').forEach(header => {
        header.addEventListener('click', () => {
            if (!searchInput) return;
            currentSearchVisible = !currentSearchVisible;
            searchInput.style.display = currentSearchVisible ? 'block' : 'none';
            if (currentSearchVisible) {
                searchInput.focus();
            } else {
                // Clear search and show all rows when hiding search
                searchInput.value = '';
                filterTable('');
            }
        });
    });

    // Sort on icon click
    document.querySelectorAll('.sort-icon').forEach(icon => {
        icon.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent header text click

            const colName = e.target.getAttribute('data-column');
            if (!colName) return;

            // Toggle direction (default ascending)
            sortDirections[colName] = !sortDirections[colName];

            sortTableByColumn(colName, sortDirections[colName]);
        });
    });

    // Filter table rows based on search input value
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            filterTable(searchInput.value);
        });
    }

    function filterTable(searchTerm) {
        const tableBody = document.querySelector('table tbody');
        if (!tableBody) return;

        const rows = Array.from(tableBody.querySelectorAll('tr'));
        const lowerSearch = searchTerm.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(lowerSearch) ? '' : 'none';
        });
    }

    function sortTableByColumn(columnName, ascending = true) {
        const tableBody = document.querySelector('table tbody');
        if (!tableBody) return;

        const headers = Array.from(document.querySelectorAll('thead th'));
        const columnIndex = headers.findIndex(th => th.textContent.trim() === columnName);
        if (columnIndex === -1) return;

        const rows = Array.from(tableBody.querySelectorAll('tr'));

        if (columnName === 'Risk Level') {
            const riskOrderAsc = ['Broken Link', 'Not Found', 'Green', 'Red'];
            const riskOrderDesc = [...riskOrderAsc].reverse();

            const order = ascending ? riskOrderAsc : riskOrderDesc;

            rows.sort((a, b) => {
                const aText = a.children[columnIndex].textContent.trim();
                const bText = b.children[columnIndex].textContent.trim();

                const aIndex = order.findIndex(r => aText.includes(r)) !== -1 ? order.findIndex(r => aText.includes(r)) : 999;
                const bIndex = order.findIndex(r => bText.includes(r)) !== -1 ? order.findIndex(r => bText.includes(r)) : 999;

                return aIndex - bIndex;
            });
        } else {
            rows.sort((a, b) => {
                const aText = a.children[columnIndex].textContent.trim().toLowerCase();
                const bText = b.children[columnIndex].textContent.trim().toLowerCase();

                if (aText < bText) return ascending ? -1 : 1;
                if (aText > bText) return ascending ? 1 : -1;
                return 0;
            });
        }

        rows.forEach(row => tableBody.appendChild(row));
    }
});


