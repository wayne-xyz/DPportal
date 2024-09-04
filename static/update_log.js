document.addEventListener('DOMContentLoaded', function() {
    fetch('/static/update_log.txt')
        .then(response => response.text())
        .then(data => {
            const lines = data.split('\n').filter(line => line.trim() !== '');
            let htmlContent = '<h3>Información de Actualización:</h3>';
            lines.forEach(line => {
                const [key, value] = line.split(':');
                if (key && value) {
                    htmlContent += `<p><strong>${key.trim()}:</strong> ${value.trim()}</p>`;
                }
            });
            document.getElementById('updateInfo').innerHTML = htmlContent;
        })
        .catch(error => {
            console.error('Error fetching update info:', error);
            document.getElementById('updateInfo').innerHTML = '<p>Información de actualización no disponible.</p>';
        });
});