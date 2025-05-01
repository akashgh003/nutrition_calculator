document.addEventListener('DOMContentLoaded', function() {
    const dishForm = document.getElementById('dish-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    if (dishForm) {
        dishForm.addEventListener('submit', function() {

            dishForm.style.display = 'none';

            loadingSpinner.style.display = 'block';

            return true;
        });
    }

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const exampleButtons = document.querySelectorAll('.recipe-example');
    if (exampleButtons.length > 0) {
        exampleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const dishInput = document.getElementById('dish-name');
                if (dishInput) {
                    dishInput.value = this.getAttribute('data-dish');
                    
                    if (dishForm) {
                        dishForm.submit();
                    }
                }
            });
        });
    }
    
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', function() {
            window.history.back();
        });
    }
});
