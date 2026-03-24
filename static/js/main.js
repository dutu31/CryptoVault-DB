document.addEventListener("DOMContentLoaded", function() {
    console.log("CryptoVault Web App loaded successfully!");
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(function() {
            alerts.forEach(function(alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000); // 5000 miliseconds
    }
});