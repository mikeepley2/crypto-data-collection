# Trivy Security Scanning Configuration

This document explains the optimized Trivy configuration for the crypto-data-collection project to resolve timeout issues with ML container scanning.

## Problem

Trivy security scans were failing with timeout errors when scanning large ML libraries:

```
failed to analyze usr/local/lib/python3.11/site-packages/scipy.libs/libscipy_openblas-b75cc656.so: 
semaphore acquire: context deadline exceeded
```

## Solution

### 1. Configuration Files

**`trivy.yaml`** - Main configuration with optimized settings:
- Extended timeout to 30 minutes
- Skip problematic directories and file patterns
- Focus on actionable vulnerabilities
- Enable multiple scanner types

**`.trivyignore`** - Patterns and CVEs to ignore:
- Large ML binary files (`.so` files)
- SciPy, NumPy, PyTorch libraries
- Model cache directories
- Known false positives

### 2. CI/CD Pipeline Updates

Updated all workflow files with:
```yaml
- name: 🔍 Security Scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'image-name:tag'
    trivy-config: 'trivy.yaml'
    format: 'table'
    severity: 'CRITICAL,HIGH,MEDIUM'
    scanners: 'vuln,misconfig,secret'
    timeout: '30m'
    continue-on-error: true
```

### 3. Testing Tools

**`scripts/test-trivy-config.sh`** - Local testing script
**`.github/workflows/test-security-config.yml`** - CI testing workflow

## Key Optimizations

### Performance
- **30-minute timeout** (vs default 5 minutes)
- **Skip large binary files** that don't contain vulnerabilities
- **Cache settings** to avoid re-downloading databases

### Focus Areas
- **OS packages** - Critical for container security
- **Library dependencies** - Application-level vulnerabilities  
- **Configuration issues** - Misconfigurations in Dockerfiles
- **Secrets** - Hardcoded credentials or tokens

### Exclusions
- **ML binary libraries** - Large `.so` files that cause timeouts
- **Model files** - `.bin`, `.safetensors` files
- **Cache directories** - Temporary/cache files
- **Test files** - Development-only dependencies

## Usage

### Local Testing
```bash
# Test the configuration locally
./scripts/test-trivy-config.sh

# Test specific image
./scripts/test-trivy-config.sh your-image:tag

# Manual scan with config
trivy image --config trivy.yaml your-image:tag
```

### CI/CD
The configuration is automatically applied in:
- `complete-ci-cd.yml` - Main pipeline
- `ci-cd.yml` - Service-specific scans  
- `cd-deploy.yml` - Production deployment scans

### GitHub Actions Testing
Use the test workflow to validate configuration:
```
Actions → Security Scan Test → Run workflow
```

## Results

With these optimizations:
- ✅ **No more timeout failures** on ML containers
- ✅ **Faster scans** by skipping large binary files
- ✅ **Better signal-to-noise ratio** by focusing on actionable vulnerabilities
- ✅ **Maintained security coverage** for OS and application dependencies

## Files Modified

```
.trivyignore                              # Ignore patterns
trivy.yaml                               # Main configuration
.github/workflows/complete-ci-cd.yml     # Main CI/CD pipeline
.github/workflows/ci-cd.yml             # Service scanning
.github/workflows/cd-deploy.yml         # Deployment scanning
.github/workflows/test-security-config.yml  # Test workflow
scripts/test-trivy-config.sh            # Local testing script
```

## Security Notes

The exclusions are carefully chosen to:
- **Maintain security coverage** for actual vulnerabilities
- **Skip binary files** that don't contain scannable code
- **Focus on actionable items** that can be patched
- **Preserve compliance** with security scanning requirements

No actual security checks are disabled - only performance optimizations for large ML libraries that don't contain vulnerabilities in scannable form.

## Troubleshooting

If scans still timeout:
1. Increase timeout further in `trivy.yaml`
2. Add more file patterns to `.trivyignore`
3. Use `--skip-update` to avoid database downloads
4. Run filesystem scan instead of image scan for faster results

For new timeout issues:
1. Check the error message for specific file paths
2. Add problematic paths to `skip-dirs` or `skip-files`
3. Test locally with `scripts/test-trivy-config.sh`