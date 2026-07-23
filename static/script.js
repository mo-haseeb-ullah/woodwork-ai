document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    const statusMsg = document.getElementById('statusMessage');
    const statusText = statusMsg.querySelector('.status-text');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const projectUrl = urlInput.value.trim();
        
        if (!projectUrl) {
            statusMsg.classList.remove('hidden');
            statusText.className = "status-text text-red-500 font-bold";
            statusText.textContent = "> Error: You must provide a project URL!";
            return;
        }

        const formData = new FormData();
        formData.append('url', projectUrl);

        // UI Loading State
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');
        statusMsg.classList.remove('hidden');
        statusMsg.classList.add('show');
        statusText.className = "status-text text-slate-500";
        statusText.textContent = "> Scraping blog post for text and images...";

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || response.statusText);
            }

            const data = await response.json();
            const taskId = data.task_id;

            // Start polling for status
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/status/${taskId}`);
                    if (!statusRes.ok) throw new Error("Failed to check status");
                    
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === 'completed') {
                        clearInterval(pollInterval);
                        
                        // Download the DOCX
                        window.location.href = `/download/${taskId}`;
                        
                        statusText.className = "status-text text-emerald-600 font-bold";
                        statusText.textContent = "> Success! Premium Plan generated and downloaded as a Word Document (.docx).";
                        
                        // Reset UI
                        submitBtn.disabled = false;
                        btnText.classList.remove('hidden');
                        spinner.classList.add('hidden');
                    } else if (statusData.status === 'error') {
                        clearInterval(pollInterval);
                        statusText.className = "status-text text-red-500 font-bold";
                        statusText.textContent = `> Error: ${statusData.error}`;
                        
                        // Reset UI
                        submitBtn.disabled = false;
                        btnText.classList.remove('hidden');
                        spinner.classList.add('hidden');
                    }
                } catch (pollError) {
                    clearInterval(pollInterval);
                    statusText.className = "status-text text-red-500 font-bold";
                    statusText.textContent = `> Polling Error: ${pollError.message}`;
                    
                    // Reset UI
                    submitBtn.disabled = false;
                    btnText.classList.remove('hidden');
                    spinner.classList.add('hidden');
                }
            }, 3000); // Poll every 3 seconds

        } catch (error) {
            statusText.className = "status-text text-red-500 font-bold";
            statusText.textContent = `> System Error: ${error.message}`;
            
            // Reset UI
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    });
});
