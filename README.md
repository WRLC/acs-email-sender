# ACS Email Sender

Azure Function to send emails via Azure Communication Services (ACS), triggered by a queue message in the function's storage account.

## Local Development

### Prerequisites

*   Python 3.12+
*   Poetry for dependency management.
*   Azure Functions Core Tools
*   Azurite local storage emulator
*   Azure Storage Explorer

### Setup and Configuration

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/WRLC/acs-email-sender.git
    cd acs-email-sender
    ```

2.  **Install dependencies:**

    ```bash
    poetry install
    source .venv/bin/activate
    ```

3.  **Configure local settings:**

    Copy `local.settings.json` from template:

    ```bash
    cp local.settings.json.template local.settings.json
    ```

    Set working values for environment variables in `local.settings.json`:

    * `ACS_CONNECTION_STRING`:  The Azure Communication Service (ACS) connection string
    * `ACS_ENDPOINT`: The ACS endpoint
    * `SENDER_EMAIL`: The configured sender email address for the ACS

4.  **Start up local function**

    ```bash
    azurite
    func start
    ```

## Deployment
Deployment to Azure is automated via GitHub Actions. The process utilizes deployment slots (e.g., `stage` and `production`) to ensure zero-downtime updates.

## Incoming Message Structure
The function is triggered by a JSON message on the `inputqueue`. The message must conform to the following structure:

```json
{
  "to": ["recipient1@example.com", "recipient2@example.com"],
  "cc": ["cc.recipient@example.com"],
  "subject": "Your Subject Here",
  "html": "<h1>Your HTML Content</h1><p>This is the HTML body of the email.</p>",
  "plaintext": "This is the plaintext body for email clients that don't support HTML."
}
```

* `to` and `subject` are required fields.
* `cc`, `html`, and `plaintext` are optional.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.