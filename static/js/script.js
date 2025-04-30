document.addEventListener('DOMContentLoaded', function() {
    // Show loading spinner when form is submitted
    const dishForm = document.getElementById('dish-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    if (dishForm) {
        dishForm.addEventListener('submit', function() {
            // Hide the form
            dishForm.style.display = 'none';
            
            // Show loading spinner
            loadingSpinner.style.display = 'block';
            
            // Submit the form
            return true;
        });
    }
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handle recipe examples
    const exampleButtons = document.querySelectorAll('.recipe-example');
    if (exampleButtons.length > 0) {
        exampleButtons.forEach(button => {
            button.addEventListener('click', function() {
                const dishInput = document.getElementById('dish-name');
                if (dishInput) {
                    dishInput.value = this.getAttribute('data-dish');
                    
                    // If we want auto-submit on example click
                    if (dishForm) {
                        dishForm.submit();
                    }
                }
            });
        });
    }
    
    // Back button functionality
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', function() {
            window.history.back();
        });
    }
});
