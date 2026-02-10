// script.js literally just for dropdowns
document.addEventListener("DOMContentLoaded", function () {
    const loginItem = document.querySelector(".sidebar-item.has-dropdown");
    if (!loginItem) return;

    const dropdown = loginItem.querySelector(".sidebar-dropdown");
    let open = false;

    loginItem.addEventListener("click", function (e) {
        e.stopPropagation();
        open = !open;
        dropdown.style.display = open ? "flex" : "none";
    });

    document.addEventListener("click", function () {
        if (open) {
            dropdown.style.display = "none";
            open = false;
        }
    });
});
