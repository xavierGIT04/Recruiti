<script>
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#evenement-form'); // ton formulaire doit avoir cet ID
    const retryBtn = document.createElement('button');
    const messageDiv = document.createElement('div');

    retryBtn.textContent = 'Réessayer';
    retryBtn.style.display = 'none';
    messageDiv.style.color = 'red';

    form.parentNode.insertBefore(messageDiv, form);
    form.parentNode.insertBefore(retryBtn, form.nextSibling);

    let formDataBackup = null;

    function submitForm() {
        const formData = new FormData(form);
        formDataBackup = new FormData(form); // backup pour réutiliser en cas de problème

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = window.location.href; // ou redirige vers la bonne URL
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            messageDiv.textContent = "Erreur de connexion. Veuillez réessayer.";
            retryBtn.style.display = 'inline-block';
        });
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm();
    });

    retryBtn.addEventListener('click', () => {
        retryBtn.style.display = 'none';
        submitForm();
    });

    window.addEventListener('online', () => {
        if (formDataBackup) {
            messageDiv.textContent = "Connexion rétablie. Tentative de soumission...";
            retryBtn.style.display = 'none';
            submitForm();
        }
    });

    window.addEventListener('offline', () => {
        messageDiv.textContent = "Vous êtes hors ligne.";
    });
});
</script>
