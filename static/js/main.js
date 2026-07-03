// Video Editing Management System main JS
document.addEventListener("DOMContentLoaded", () => {
    // ----------------------------------------
    // 1. Theme Configuration (Dark / Light Mode)
    // ----------------------------------------
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeIcon = document.getElementById("theme-toggle-icon");
    const currentTheme = localStorage.getItem("theme") || "dark"; // Default to dark mode

    // Apply the active theme
    applyTheme(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const activeTheme = document.body.classList.contains("dark-mode") ? "light" : "dark";
            applyTheme(activeTheme);
        });
    }

    function applyTheme(theme) {
        if (theme === "dark") {
            document.body.classList.remove("light-mode");
            document.body.classList.add("dark-mode");
            localStorage.setItem("theme", "dark");
            if (themeIcon) {
                themeIcon.className = "fas fa-sun";
            }
        } else {
            document.body.classList.remove("dark-mode");
            document.body.classList.add("light-mode");
            localStorage.setItem("theme", "light");
            if (themeIcon) {
                themeIcon.className = "fas fa-moon";
            }
        }
    }

    // ----------------------------------------
    // 2. Mobile Sidebar Navigation Toggle
    // ----------------------------------------
    const sidebarToggleBtn = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("sidebar");
    const appContainer = document.querySelector(".app-container");

    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("show");
            if (appContainer) {
                appContainer.classList.toggle("sidebar-open");
            }
        });
    }

    // Close sidebar on small screen clicking outside
    document.addEventListener("click", (e) => {
        if (window.innerWidth < 992 && sidebar && sidebar.classList.contains("show")) {
            if (!sidebar.contains(e.target) && e.target !== sidebarToggleBtn) {
                sidebar.classList.remove("show");
                if (appContainer) {
                    appContainer.classList.remove("sidebar-open");
                }
            }
        }
    });

    // ----------------------------------------
    // 3. Dynamic Price Fetching & Calculations
    // ----------------------------------------
    // Elements in Add Work / Edit Work modals
    const serviceSelect = document.getElementById("work-service-select");
    const priceInput = document.getElementById("work-price");
    const qtyInput = document.getElementById("work-quantity");
    const totalInput = document.getElementById("work-total");

    // Fetch price when service is chosen
    if (serviceSelect && priceInput) {
        serviceSelect.addEventListener("change", () => {
            const serviceId = serviceSelect.value;
            if (serviceId) {
                fetch(`/api/services/${serviceId}/price`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error("Network response was not OK");
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data && data.price !== undefined) {
                            priceInput.value = data.price;
                            calculateTotal();
                        }
                    })
                    .catch(err => {
                        console.error("Error fetching price:", err);
                    });
            } else {
                priceInput.value = "0";
                calculateTotal();
            }
        });
    }

    // Update total calculation when qty or price changes
    if (qtyInput) qtyInput.addEventListener("input", calculateTotal);
    if (priceInput) priceInput.addEventListener("input", calculateTotal);

    function calculateTotal() {
        if (qtyInput && priceInput && totalInput) {
            const qty = parseInt(qtyInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0.0;
            totalInput.value = (qty * price).toFixed(2);
        }
    }
});
