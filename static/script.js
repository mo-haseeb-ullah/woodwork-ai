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
                        
                        statusText.className = "status-text text-emerald-600 font-bold mb-4";
                        statusText.textContent = "> Success! Premium Plan generated with images embedded and available for download.";
                        
                        // Setup dual download buttons
                        downloadDocxBtn.href = `/download/${taskId}`;
                        downloadDocxBtn.onclick = null;
                        
                        downloadContainer.classList.remove('hidden');
                        downloadContainer.classList.add('flex');
                        
                        // Auto trigger docx download
                        window.location.href = `/download/${taskId}`;
                        
                        // Reset UI
                        submitBtn.disabled = false;
                        btnText.classList.remove('hidden');
                        spinner.classList.add('hidden');
                    } else if (statusData.status === 'error') {
                        clearInterval(pollInterval);
                        statusText.className = "status-text text-red-500 font-bold mb-4";
                        statusText.textContent = `> Error: ${statusData.error}`;
                        
                        // Reset UI
                        submitBtn.disabled = false;
                        btnText.classList.remove('hidden');
                        spinner.classList.add('hidden');
                    }
                } catch (pollError) {
                    clearInterval(pollInterval);
                    statusText.className = "status-text text-red-500 font-bold mb-4";
                    statusText.textContent = `> Polling Error: ${pollError.message}`;
                    
                    // Reset UI
                    submitBtn.disabled = false;
                    btnText.classList.remove('hidden');
                    spinner.classList.add('hidden');
                }
            }, 3000);

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

