document.addEventListener("DOMContentLoaded", function() {
    const alerts = document.querySelectorAll(".alert");

    if (alerts.length > 0) {
        setTimeout(function() {
            alerts.forEach(function(alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            });
        }, 5000);
    }

    const algorithmSelect = document.getElementById("algorithmSelect");
    const keySelect = document.getElementById("keySelect");

    if (algorithmSelect && keySelect) {
        const originalOptions = Array.from(keySelect.options).map(function(option) {
            return option.cloneNode(true);
        });

        function filterKeys() {
            const selectedAlgorithmId = algorithmSelect.value;

            keySelect.innerHTML = "";

            const placeholder = document.createElement("option");
            placeholder.value = "";
            placeholder.textContent = selectedAlgorithmId ? "Selectează cheia" : "Selectează mai întâi algoritmul";
            keySelect.appendChild(placeholder);

            originalOptions.forEach(function(option) {
                if (option.value && option.dataset.algorithmId === selectedAlgorithmId) {
                    keySelect.appendChild(option.cloneNode(true));
                }
            });

            keySelect.value = "";
        }

        algorithmSelect.addEventListener("change", filterKeys);
        filterKeys();
    }
});
