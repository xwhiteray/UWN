// Define the base URL of your server
const baseURL = 'https://172.104.41.186:5000';
// const baseURL = 'http://localhost:5000'

// Create an instance of Html5Qrcode
const html5QrCode = new Html5Qrcode("qr-reader");

let miniCards = [];

// Define the scan callbacks
const qrCodeSuccessCallback = (decodedText, decodedResult) => {
    console.log(`QR Code detected: ${decodedText}`);

    // Stop the scanner to prevent multiple scans
    html5QrCode.stop().then(() => {
        // QR Code scanning is stopped.
    }).catch(err => {
        console.error('Failed to stop scanning:', err);
    });

    // Show the scan button
    const scanButton = document.getElementById('scan-button');
    scanButton.style.display = 'inline-block'; // Show the button

    // Send the transaction ID to the server for verification
    verifyTransaction(decodedText.trim());
};

// Function to start scanning again
const startScanning = () => {
    const scanButton = document.getElementById('scan-button');
    scanButton.style.display = 'none'; // Hide the button

    // Start scanning
    const config = { fps: 10, qrbox: 250 };
    html5QrCode.start(
        { facingMode: "environment" }, // cameraIdOrConfig
        config,
        qrCodeSuccessCallback,
        qrCodeErrorCallback
    ).catch(err => {
        // Handle errors starting the scanner
        console.error('Error starting Html5Qrcode:', err);
    });
};

// Event listener for the scan button
document.getElementById('scan-button').addEventListener('click', startScanning);

// Function to send a request to give Gelang
function giveGelang(transactionId, buttonElement) {
    // Optionally, confirm the action with the user
    // const confirmAction = confirm(`Are you sure you want to mark GELANG as "Yes" for Transaction ID: ${transactionId}?`);
    // if (!confirmAction) return;

    // Disable the button to prevent multiple clicks
    buttonElement.disabled = true;
    buttonElement.textContent = 'Updating...';

    // Prepare the request payload
    const payload = {
        transaction_id: transactionId,
        // api_key: 'your_secure_api_key_here'  // Include if implementing API key authentication
    };

    // Send a POST request to the server
    fetch(`${baseURL}/give-gelang`, {  // Using relative URL since served from same origin
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // alert(data.message);
                // Optionally, update the GELANG cell in the table to "Yes"
                updateGelangStatusInTable(transactionId);
                buttonElement.textContent = 'Hadir';

                // Create a mini card
                let color = buttonElement.dataset.color;
                let seats = buttonElement.dataset.seats;

                let miniCard = {
                    color: color,
                    seats: seats
                };

                // Add the mini card to the array
                miniCards.push(miniCard);

                // Render the mini cards
                renderMiniCard(miniCard);

                // Start scanning again automatically
                startScanning();

                // Hide the "Scan Again" button if it's visible
                const scanButton = document.getElementById('scan-button');
                scanButton.style.display = 'none';
            } else {
                alert(`Failed to give Gelang: ${data.message}`);
                buttonElement.disabled = false;
                buttonElement.textContent = 'Give Gelang';
            }
        })
        .catch(error => {
            console.error('Error giving Gelang:', error);
            alert('An error occurred while giving Gelang.');
            buttonElement.disabled = false;
            buttonElement.textContent = 'Give Gelang';
        });
}

function renderMiniCard(card) {
    let miniCardsContainer = document.getElementById('mini-cards-container');
    if (!miniCardsContainer) {
        miniCardsContainer = document.createElement('div');
        miniCardsContainer.id = 'mini-cards-container';
        // Append to resultDiv
        const resultDiv = document.getElementById('result');
        resultDiv.appendChild(miniCardsContainer);
    }

    const cardDiv = document.createElement('div');
    cardDiv.className = 'mini-card';

    const colorIndicator = document.createElement('div');
    colorIndicator.className = 'color-indicator';
    let color = '';
    if (card.color == 'KUNING') {
        color = 'yellow';
    } else if (card.color == 'MERAH') {
        color = 'red';
    } else if (card.color == 'HIJAU') {
        color = 'green';
    } else {
        color = 'blue';
    }

    colorIndicator.style.backgroundColor = color;

    const cardContent = document.createElement('div');
    cardContent.className = 'card-content';

    const colorText = document.createElement('div');
    colorText.textContent = `Color: ${card.color}`;

    const seatsText = document.createElement('div');
    seatsText.textContent = `Seats: ${card.seats}`;

    cardContent.appendChild(colorText);
    cardContent.appendChild(seatsText);

    cardDiv.appendChild(colorIndicator);
    cardDiv.appendChild(cardContent);

    // Prepend the new card to the container
    miniCardsContainer.insertBefore(cardDiv, miniCardsContainer.firstChild);
}


// Function to update the GELANG status in the table without refreshing
function updateGelangStatusInTable(transactionId) {
    const table = document.getElementById('transaction-table');
    if (!table) return;

    // Iterate through table rows to find all matching transactions
    const rows = table.getElementsByTagName('tr');
    for (let i = 1; i < rows.length; i++) {  // Start from 1 to skip header row
        const cells = rows[i].getElementsByTagName('td');
        const ketValue = cells[headersIndex('KET')].textContent.trim();
        if (ketValue === transactionId) {
            cells[headersIndex('GELANG')].textContent = 'Yes';
        }
    }
}

// Helper function to get the index of a header
function headersIndex(headerName) {
    const table = document.getElementById('transaction-table');
    if (!table) return -1;

    const headers = table.getElementsByTagName('th');
    for (let i = 0; i < headers.length; i++) {
        if (headers[i].textContent.trim().toUpperCase() === headerName.toUpperCase()) {
            return i;
        }
    }
    return -1;
}


// Function to send the transaction ID to the server
function verifyTransaction(transactionId) {
    // Display a loading message
    const resultDiv = document.getElementById('result');
    resultDiv.textContent = 'Verifying transaction...';
    resultDiv.className = '';

    // Send a POST request to the server
    fetch(`${baseURL}/verify-transaction`, {  // Using relative URL since served from same origin
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ transaction_id: transactionId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Transaction is valid
                resultDiv.textContent = '';
                resultDiv.className = 'success';
                // Display the transaction details
                displayTransactionDetails(data.details);
            } else {
                // Transaction is invalid
                resultDiv.textContent = `Verification failed: ${data.message}`;
                resultDiv.className = 'failure';
            }
        })
        .catch(error => {
            console.error('Error verifying transaction:', error);
            resultDiv.textContent = 'An error occurred during verification.';
            resultDiv.className = 'failure';
        });
}

// Function to display the transaction details in a table
function displayTransactionDetails(details) {
    // Create a table element
    const table = document.createElement('table');
    table.id = 'transaction-table';

    // Get the headers from the first detail object
    const headers = Object.keys(details[0]);

    // Create the table header row
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    // Add an additional header for the "Give Gelang" button
    const actionTh = document.createElement('th');
    actionTh.textContent = 'Action';
    headerRow.appendChild(actionTh);

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create the table body
    const tbody = document.createElement('tbody');

    details.forEach(detail => {
        const row = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            let cellValue = detail[header];

            // Format currency fields
            if (header === 'NILAI' || header === 'AMOUNT') {
                const num = parseFloat(cellValue);
                if (!isNaN(num)) {
                    cellValue = `$${num.toFixed(2)}`;
                }
            }

            // Format date fields (assuming format is DD/MM/YYYY)
            if (header === 'TGL BAYAR') {
                const dateParts = cellValue.split('/');
                if (dateParts.length === 3) {
                    const formattedDate = `${dateParts[1]}/${dateParts[0]}/${dateParts[2]}`;
                    cellValue = formattedDate; // Convert to MM/DD/YYYY or desired format
                }
            }

            td.textContent = cellValue;
            td.setAttribute('data-label', header); // Add data-label attribute
            row.appendChild(td);
        });

        // Add the "Give Gelang" button
        const actionTd = document.createElement('td');
        const giveGelangButton = document.createElement('button');
        giveGelangButton.textContent = 'Give Gelang';
        giveGelangButton.className = 'give-gelang-button';
        giveGelangButton.dataset.transactionId = detail['KET'];  // Assuming 'KET' is the unique ID

        // Add data attributes for color and seats
        giveGelangButton.dataset.color = detail['WARNA'] || 'blue'; // Default color
        giveGelangButton.dataset.seats = detail['BARIS'] + detail['NO KURSI'] || '1';    // Default seats
        actionTd.appendChild(giveGelangButton);
        actionTd.setAttribute('data-label', 'Action'); // Add data-label attribute
        row.appendChild(actionTd);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    // Append the table to a container
    const container = document.createElement('div');
    container.classList.add('table-container'); // Add the table-container class
    container.appendChild(table);

    // Append the table to the resultDiv
    const resultDiv = document.getElementById('result');

    // Remove any existing table before appending a new one
    const existingTableContainer = resultDiv.querySelector('.table-container');
    if (existingTableContainer) {
        existingTableContainer.remove();
    }

    resultDiv.appendChild(container);

    // Attach event listeners to all "Give Gelang" buttons
    attachGiveGelangEventListeners();
}

// Function to attach event listeners to "Give Gelang" buttons
function attachGiveGelangEventListeners() {
    const buttons = document.querySelectorAll('.give-gelang-button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const transactionId = button.dataset.transactionId;
            giveGelang(transactionId, button);
        });
    });
}

const qrCodeErrorCallback = (errorMessage) => {
    // Handle scan failure
    console.warn(`QR Code scan error: ${errorMessage}`);
};

// Start scanning
const config = { fps: 10, qrbox: 250 };
html5QrCode.start(
    { facingMode: "environment" }, // cameraIdOrConfig
    config,
    qrCodeSuccessCallback,
    qrCodeErrorCallback
).catch(err => {
    // Handle errors starting the scanner
    console.error('Error starting Html5Qrcode:', err);
});
