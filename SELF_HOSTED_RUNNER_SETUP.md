# Self-Hosted GitHub Runner Setup

Since your K3s cluster runs locally, the best solution is to use a self-hosted GitHub Actions runner on your machine.

## Setup Steps:

1. **Go to your GitHub repository**: https://github.com/mikeepley2/crypto-data-collection

2. **Navigate to Settings → Actions → Runners**

3. **Click "New self-hosted runner"**

4. **Select Linux** and follow the download/configuration commands provided

5. **Install the runner** (example commands - use the exact ones from GitHub):
   ```bash
   cd ~
   mkdir actions-runner && cd actions-runner
   curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
   tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
   ```

6. **Configure the runner**:
   ```bash
   ./config.sh --url https://github.com/mikeepley2/crypto-data-collection --token <TOKEN_FROM_GITHUB>
   ```

7. **Start the runner**:
   ```bash
   ./run.sh
   ```
   
   Or install as a service:
   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

8. **Update your workflow files** to use the self-hosted runner by changing:
   ```yaml
   runs-on: ubuntu-latest
   ```
   to:
   ```yaml
   runs-on: self-hosted
   ```

## Benefits:
- Direct access to your local K3s cluster at 127.0.0.1:6443
- No need to expose K3s to the internet
- Faster deployments (no need to transfer large images)
- More secure (all traffic stays local)

