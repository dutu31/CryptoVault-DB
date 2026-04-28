document.addEventListener("DOMContentLoaded", function() {
    const alerts = document.querySelectorAll(".alert");

    if (alerts.length > 0) {
        setTimeout(function() {
            alerts.forEach(function(alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
    }

    const algorithmSelect = document.getElementById("algorithmSelect");
    const keySelect = document.getElementById("keySelect");

    if (algorithmSelect && keySelect) {
        function filterKeys() {
            const selectedAlgorithmId = algorithmSelect.value;
            let firstVisibleOption = null;

            Array.from(keySelect.options).forEach(function(option) {
                if (option.dataset.algorithmId === selectedAlgorithmId) {
                    option.hidden = false;
                    option.disabled = false;

                    if (firstVisibleOption === null) {
                        firstVisibleOption = option;
                    }
                } else {
                    option.hidden = true;
                    option.disabled = true;
                }
            });

            if (firstVisibleOption !== null) {
                keySelect.value = firstVisibleOption.value;
            } else {
                keySelect.value = "";
            }
        }

        algorithmSelect.addEventListener("change", filterKeys);
        filterKeys();
    }
});