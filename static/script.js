document.addEventListener('DOMContentLoaded', () => {
    const urlContainer = document.getElementById('urlContainer');
    const urlInput = document.getElementById('urlInput');
    
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    
    const statusMsg = document.getElementById('statusMessage');
    const statusText = statusMsg.querySelector('.status-text');
    const downloadContainer = document.getElementById('downloadContainer');
    const downloadDocxBtn = document.getElementById('downloadDocxBtn');

    let currentMode = 'url'; // 'url'


    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        downloadContainer.classList.add('hidden');

        const formData = new FormData();
        formData.append('mode', currentMode);

        if (currentMode === 'url') {
            const projectUrl = urlInput.value.trim();
            if (!projectUrl) {
                statusMsg.classList.remove('hidden');
                statusMsg.classList.add('opacity-100', 'translate-y-0');
                statusText.className = "status-text text-red-500 font-bold mb-4";
                statusText.textContent = "> Error: Please provide a project URL!";
                return;
            }
            formData.append('url', projectUrl);
        }

        // UI Loading State
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');
        statusMsg.classList.remove('hidden');
        statusMsg.classList.add('opacity-100', 'translate-y-0');
        statusText.className = "status-text text-slate-500 font-medium mb-4";
        statusText.textContent = currentMode === 'url' 
            ? "> Scraping blog post for text and images..." 
            : "> Parsing PDF pages, extracting images, and processing with AI...";

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMsg = response.statusText;
                try {
                    const errorData = await response.json();
                    if (errorData.error) errorMsg = errorData.error;
                } catch (e) {}
                throw new Error(errorMsg);
            }

            // Extract filename from Content-Disposition header
            let filename = "Premium_Plan.docx";
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            // Get binary data
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            statusText.className = "status-text text-emerald-600 font-bold mb-4";
            statusText.textContent = "> Success! Premium Plan generated and downloaded.";
            
            downloadDocxBtn.href = url;
            downloadDocxBtn.download = filename;
            downloadDocxBtn.onclick = null;
            
            downloadContainer.classList.remove('hidden');
            downloadContainer.classList.add('flex');
            
            // Auto trigger docx download properly with the correct filename
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Reset UI
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');

        } catch (error) {
            statusText.className = "status-text text-red-500 font-bold mb-4";
            statusText.textContent = `> System Error: ${error.message}`;
            
            // Reset UI
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    });
});

