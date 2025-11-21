# 🚀 GitHub Actions CI/CD Setup Guide

## Step 1: Repository Secrets Configuration

Copy and add these secrets to your GitHub repository:

### 🔐 Navigate to Repository Settings
1. Go to your GitHub repository: `https://github.com/mikeepley2/crypto-data-collection`
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 📋 Required Secrets

#### **K3S_KUBECONFIG**
```
Value: YXBpVmVyc2lvbjogdjEKY2x1c3RlcnM6Ci0gY2x1c3RlcjoKICAgIGNlcnRpZmljYXRlLWF1dGhvcml0eS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJEUlZKVVNVWkpRMEZVUlMwdExTMHRDazFKU1VNdmFrTkRRV1ZoWjBGM1NVSkJaMGxDUVVSQlRrSm5hM0ZvYTJsSE9YY3dRa0ZSYzBaQlJFRldUVkpOZDBWUldVUldVVkZFUlhkd2NtUlhTbXdLWTIwMWJHUkhWbnBOUWpSWVJGUkpNVTFVUVhoT1JFbDRUa1JSZWs5V2IxaEVWRTB4VFZSQmVFMXFTWGhPUkZGNlQxWnZkMFpVUlZSTlFrVkhRVEZWUlFwQmVFMUxZVE5XYVZwWVNuVmFXRkpzWTNwRFEwRlRTWGRFVVZsS1MyOWFTV2gyWTA1QlVVVkNRbEZCUkdkblJWQkJSRU5EUVZGdlEyZG5SVUpCVGs1NUNraHNORnBJZUhSb1ZYWklXRXBXWTFkblVqZE9RbGR2WlZRMGFqSktiREl5U1dSSFNYZHZMMjkwZVdOUlEyUkRVemRCWW1wRVEwUTFTbE5aYjJwYVdrd0tSVkZtU1hWM1dUZGlOV1pxVVhSVVNpOW1LeXMzVG5oTGJGTjJjbUl6UlRVMGRXdzJhRXh1Y0UxQkwybFRZMk53VFhoMVFuVmFVazlCVHpWVlVHazJPUXBYZWpCNFF6TklXaXMxUVc5elVDOVVXVVZYTUV0NlptaE1NVEpHYVVSc1ZrcFdRWEEzYkRkeWREUnVhM0ZXUTNBeWJYTXZlaXRCZGtoV0sxUTNaME53Q25WeE9UWkJOR3A1Tm1Wa01IQXplVVp5V21VeVZGSkJUMDVxYkhaUGJWRm1iVEE1WW5waFlYTk1WeTlPYkVFME1GQnRaVTlVWTNKc05rOHdabkpKTldZS1ZWTndkMW8yZUUwcmVsVnVOVWhIY2pOR05EQmtiRVZ3VEZOU2NVUjZkMGhKT1U5RmVVVnhNR2R5Y3pod2EwNHplVWhqU1ZwMmMwaFJRM0I0V0d0MFJBcDBkV0l6YlVNMWJFZGhSbmhuUjJkMWMwNDRRMEYzUlVGQllVNWFUVVpqZDBSbldVUldVakJRUVZGSUwwSkJVVVJCWjB0clRVRTRSMEV4VldSRmQwVkNDaTkzVVVaTlFVMUNRV1k0ZDBoUldVUldVakJQUWtKWlJVWlBjVzVFUzJSM2FrSlNOMnRMTVhsTldHdE5UMFpvTm1OUVVGTk5RbFZIUVRGVlpFVlJVVThLVFVGNVEwTnRkREZaYlZaNVltMVdNRnBZVFhkRVVWbEtTMjlhU1doMlkwNUJVVVZNUWxGQlJHZG5SVUpCUlZSMlpWWXpOM3BQYUhWQmRuSlFURGRoS3dwcGExZGtRM2wyVjNkRGVHWXhPRTFUYVZFM1p6bG9ka1JsTDJseFNsTkxNemwzY2psTlNXRlZiRmh3UmsxdVVHRlJlakF2V0hNMmRuTTJPVFpOUTFrNUNqQkxWbWcwYlc1MloySXlPVGRLUVhwdE5rdGhZbEZUYVVneVpHWjVNamR6YjFadlRUZzNSVFEySzNsU1NXcEJVRVkwTHpoaEt5OTBha2htU21SSFMxRUtPVWw1Ym01TFZVRkZOMjlIWWswNFRGSnFTbnBPZERRNVpXUkljRVV3WkdkWFJYbE5WSE40ZEZOemVWUldiSGMxT1ZvMVYyNWFTMnQ2Y1ZSWmRVdEJWQXBIUVZCSGJHVlVNV2wxUldKeldITmplVGx5VTFWNmFGaGtVVWw2YlRreFlrZzRSM2x0TVdsWk1rcElXblF4VVVaS1kxVTVLMVpIUldkb1ZtaDZXSEZ3Q25GT2MweExVelZHU2tsd015dHhRbU5zZFVOc1QwUllTM0ZEY1dONFVsa3ZVMVJuVm5wSGVrMUllVTl6U2pBNGJsRnJhM1ozUzAxd1dtaHdXbk5uVm5RS2FrYzRQUW90TFMwdExVVk9SQ0JEUlZKVVNVWkpRMEZVUlMwdExTMHRDZz09CiAgICBzZXJ2ZXI6IGh0dHBzOi8vMTI3LjAuMC4xOjY0NDMKICBuYW1lOiBjcnlwdG9haS1rOHMtdHJhZGluZy1lbmdpbmUKY29udGV4dHM6Ci0gY29udGV4dDoKICAgIGNsdXN0ZXI6IGNyeXB0b2FpLWs4cy10cmFkaW5nLWVuZ2luZQogICAgdXNlcjoga3ViZXJuZXRlcy1hZG1pbgogIG5hbWU6IGt1YmVybmV0ZXMtYWRtaW5AY3J5cHRvYWktazhzLXRyYWRpbmctZW5naW5lCmN1cnJlbnQtY29udGV4dDoga3ViZXJuZXRlcy1hZG1pbkBjcnlwdG9haS1rOHMtdHJhZGluZy1lbmdpbmUKa2luZDogQ29uZmlnCnByZWZlcmVuY2VzOiB7fQp1c2VyczoKLSBuYW1lOiBrdWJlcm5ldGVzLWFkbWluCiAgdXNlcjoKICAgIGNsaWVudC1jZXJ0aWZpY2F0ZS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJEUlZKVVNVWkpRMEZVUlMwdExTMHRDazFKU1VSSlZFTkRRV2R0WjBGM1NVSkJaMGxKUzBkVmFXaGphR1EzU1RSM1JGRlpTa3R2V2tsb2RtTk9RVkZGVEVKUlFYZEdWRVZVVFVKRlIwRXhWVVVLUVhoTlMyRXpWbWxhV0VwMVdsaFNiR042UVdWR2R6QjVUbFJGZDAxVVVYbE5WRkV3VFhwc1lVWjNNSGxPYWtWM1RWUlJlVTFVVVRCT1JFcGhUVVJSZUFwR2VrRldRbWRPVmtKQmIxUkViazQxWXpOU2JHSlVjSFJaV0U0d1dsaEtlazFTYTNkR2QxbEVWbEZSUkVWNFFuSmtWMHBzWTIwMWJHUkhWbnBNVjBackNtSlhiSFZOU1VsQ1NXcEJUa0puYTNGb2EybEhPWGN3UWtGUlJVWkJRVTlEUVZFNFFVMUpTVUpEWjB0RFFWRkZRWGx4WTJodWRuVlVhMGhWVjJoTFFub0thVzVYUkVKbmJreHhlWEZXY2xocFNHMHZUVVJZZEN0eWJqbHFaSFJQWVRacU9IVm5WekJtT1VFeU5tWjZSbFZ5ZG0xeVozRnNaWEJ4TDBaM1RtSk5RUXB6TjNGVFN5OUVTbTVvV1ZOUWNXOW5NMkpFUzFOT1pXRjBOV2xXTWxaRWRsWlFPVGRyVmxwV2NVSXplbXc0ZEZkYVNFUTFRMEpyVjJWeFpHNXVVSGRMQ2tWWVZsRkdlalJWZGtKNWRXbFRiVFJHZVZKTFpETjVhV1pCYkdSb1lTOVpPVWR6SzBsRFRrRmpVa1JrZGtwU2RFUjNUR1p1TkZSM05sSjFNVXc1U0V3S2NGWjFhRVkwYkdSbWNFbGxWbEl6WkVkbVluTm5TSHAyZDFkRU9YVlVSV05OVDNob2R6QlhaM1pPUldZd04yUnZkbEZDSzBaM1VVZFFaMnhNZEdwRE5ncHBXbEkxWldFME5FdFZhbUYzY2xad2RHd3lVMWd6UzFOMlR6UlVRMGcxZEM5V1IzRm9UV05JUTFSVlRtaG9jWFJpWWt0TllWZEpWak5yT0hKVlQwZzRDbTFxU0docVVVbEVRVkZCUW04eFdYZFdSRUZQUW1kT1ZraFJPRUpCWmpoRlFrRk5RMEpoUVhkRmQxbEVWbEl3YkVKQmQzZERaMWxKUzNkWlFrSlJWVWdLUVhkSmQwUkJXVVJXVWpCVVFWRklMMEpCU1hkQlJFRm1RbWRPVmtoVFRVVkhSRUZYWjBKVWNYQjNlVzVqU1hkVlpUVkRkR05xUmpWRVJHaFpaVzVFZWdvd2FrRk9RbWRyY1docmFVYzVkekJDUVZGelJrRkJUME5CVVVWQmRVVmhXWGhYYVZwM05qRjNiRlIxVkRVd1owOUhRMDlUVUN0cWJXd3pNSGRwZVZBdkNpdGxhVWxKTVZsaGMzcDVhWGt3VUU1d01tc3ZhWFozZUdOM1lqTmxabVExU1Vsd2NFaExiVW95Um1wb09HcGpVakE0ZW1SRWNXVllZVXczY1M5MVUyZ0tUVlZUY1hGeFJsWkZielpMU21SM2FWTkJUbEJKWVhOTmRWQXpiaTlSZWxCWWIxQklPVVF3WkZZMWFUZFJUWGhXUkVKdVV6TmhUVmxNZFRVeUwyWnRiZ296TmpWM2Jtb3laRlYwVm0xT1MwUTVVa0ZaVVVGWlR6SnBLMDVoZGt4dFl5OVVkblZVWlVoU1EwczNiSEpFTUZOVFYwRlphekZwYm5oRGRESkxTWEZYQ2l0SlRHVkhZM3BZV2pSTVRYWlpPV3BUZVVKMU5qVnpTVnBWY0dzMWEyNUJLelIzVlZKdVpGSXhUelpqU0hKMVVXcGlVMHMxUlZGaFVYZFVTRWxOWjJVS1Z6bHFUblJNTlM5bE4xcDJkSEpUTm1JM1RYZGpRVlI1ZG5Jd01rOUZhMUpEVUhKTFdUbG1TSEZ1VEdRMVVIVk5kbEU5UFFvdExTMHRMVVZPUkNCRFJWSlVTVVpKUTBGVVJTMHRMUzB0Q2c9PQogICAgY2xpZW50LWtleS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJTVTBFZ1VGSkpWa0ZVUlNCTFJWa3RMUzB0TFFwTlNVbEZiM2RKUWtGQlMwTkJVVVZCZVhGamFHNTJkVlJyU0ZWWGFFdENlbWx1VjBSQ1oyNU1jWGx4Vm5KWWFVaHRMMDFFV0hRcmNtNDVhbVIwVDJFMkNtbzRkV2RYTUdZNVFUSTJabnBHVlhKMmJYSm5jV3hsY0hFdlJuZE9ZazFCY3pkeFUwc3ZSRXB1YUZsVFVIRnZaek5pUkV0VFRtVmhkRFZwVmpKV1JIWUtWbEE1TjJ0V1dsWnhRak42YkRoMFYxcElSRFZEUW10WFpYRmtibTVRZDB0RldGWlJSbm8wVlhaQ2VYVnBVMjAwUm5sU1MyUXplV2xtUVd4a2FHRXZXUW81UjNNclNVTk9RV05TUkdSMlNsSjBSSGRNWm00MFZIYzJVblV4VERsSVRIQldkV2hHTkd4a1puQkpaVlpTTTJSSFptSnpaMGg2ZG5kWFJEbDFWRVZqQ2sxUGVHaDNNRmRuZGs1RlpqQTNaRzkyVVVJclJuZFJSMUJuYkV4MGFrTTJhVnBTTldWaE5EUkxWV3BoZDNKV2IzUnNNbE5ZTTB0VGRrODBWRU5JTlhRS0wxWkhjV2hOWTBoRFZGVk9hR2h4ZEdKaVMwMWhWMGxXTTJzNGNsVlBTRGh0YWtob2FsRkpSRUZSUVVKQmIwbENRVkZETURSTE16WnNMMDlwTmxVNE5nb3JNMlZHUzNSUVUycFBWM3BzYVZCWmJrazNNVzA1WW5wV1JrbzRUSFpZWTBwSFFqWlFhbUZZYjNNMWNYaE5PWFZqYzNKRVppdFBaRkoyWkZSWFFVWmxDbVpNU0hkMVYwMUZVWHAyUW14V1QyUnBVRFJwZDFWM1lqZG5lbFJQUTJKMmRTOVRVMlZwU2xKdE5ubERha3BHUTJWRFVscE1RbWx4Y1V4SVQzTnBTMmtLUmt4bWNqQjZhVEJPYURST2RFMHZNemQ2ZFROMFFsZG1VbkZvUldGblRXNXNiRFF2ZEZONldFWm5Xa3RpTm1nNVYzbFpWVTFCYm5sQ1JVRjBNbmhxYkFwUFNuRkdZVE0yVTNsRk4ySTNSRmRtYTI5VlZUa3JUVFJaUmpoT1ZUZzRVVzlGZEdsMGVXeExZV3MwTlRGemFIVklSSEp1Vkc1eFlUTlBjeXREYlZwMENrMVFlRlZyUjIxRlRUTjZjbEJEVTFRek1rZFBSM1Y0WWxGS1pEZzJRMDFNVkdKbmVGSnhOMnRqUlZkMFlqOTZXV1l6UTJKRUwyUllMMjR2YjJkb1RIWUtSV05rVldScVNHeEJiMGRDUVZCdlRpdGxaV3BUTE85Q2QwOXJWbWRzVURaWlVTczRUbXczVm14aFNEVnRXSGxUYUZVclQzWlhWakZOWTFoTlRHTnpWd3B0T0RKRFMxWnZObTV2WmtsVFREUllUSFp2TVdkRldYaHpTVTQzWXpGellXdzRWRXBqTVROT1JYTkJOV016ZVRacVpXbGpUMlIxYWpFdlJHeHVjMEowQ2twNWN6Vk9SSEJhTVZrMlVVSjFWWEpNY1RSMkt6WnFSbFpvY2tOeWJVTXZUM2RUTXpkYVFXbHBPVzVvYTBSeVJuUk5VM2x2VFdsNlFXOUhRa0ZOT1RRS2IyTkZPSEZhWTFOWlpVWk1PVnBzY1ROaE5DOUxORkJpVVVkUVRVMUpaMVZ0TWpZek0xSnRLeTh3VHpCQllXOXNOMDFzVDBsRVFtdG5OMEkyY25kTGR3cFpVVmhSZEhVMlJESjJabVpCY0ZKdldHUnFaRlppVVVsSGRtcElUemhEWmtOeVUzSkZZM0pOT0dFM2FERnRkRzVSYVRSamQyMDRhMVU1VG5CTlN5dHJDbEEwVkhGNFlpOTVhbGxtTHpGTU5qWlBXR3BRTkhKV1pYRktVbTVxY2tWYVFtUlJhVkJWWlM5QmIwZEJUemhCVkUxNFMwWXJVR1pOVkU5WWFUSnZXVGtLYjNwRWNVaFJZMVZXYW5ZMlVGSlpWak5OYWxNMFQyUTVSR1ZMV1VoeGMzTldOVXdyY0hCNlZGQk5ZazVRZERkNlZISTFlVUpHVUdwU1kyVTVOMDF6VWdvNFQyWnBUbFYyU0dGNk9WQktWVXNyYm1oTFYydE1SVFUzUlc5NVFWQkZWVXAyVUc5VmRtdGpWM0JDTXpGV1RGbFBTemh0YURGSFFVaGhlbVpXYVdKaUNuZ3lhbUo2TVVWNE9HTktRVmxKY2xabmVISmlOa3ByUTJkWlFsTlZPVmx6VEdaNFJpOUlPVzEyV2s5d01qSlJORkJ6ZW5aME9VMXVVblZIUkZCc2IyNEtXakJMVUdOMVJYTmFiMDgyYkhVMFRrODNheXRQYzFObVFsTXZjR0V3UVRBMVNYVlRkbXBRYmpWR1JFeDJNVnAxVG1aYVMxTkhWV0pxTUZCQmRtUjFjZ3B6WVRaUWQxSXJkV1VyVG5kSWVuUTVkazR2VXpWeFJqQTFUM0o1TlRoU2F6VkNlWGRtU0d3MVNFTlhOWGRaUVVreGMxWndibnBTWVVnelNHRkNUVzU0Q2xWa2VuUldVVXRDWjBaM2VIZERhVEJsVHpCS1kxWndlVTVwWW5CT0swMUhaM2hNVTFJd2NVVkpVR0ZPVVVsM1QxWnlaMlI0UjBKeGRXMTViVXc1WmtVS2JGaGxkeXM0ZDBsd2NYcEhibTVDUjFaQ1kxaFhRVWxqUTBKaUsxUnlORWhsUTJsNVVUZE5XRkppY0ZSeGRESnJaVWwzVUVVeWNFOVhPVkIzVGpoVGN3cEdVRE01WnpKTFF6UTVPQzlUVldWbFlrNVlObXRtTW5FMVNGTjZaRkJXY1UxdlNqZGlOMjQ1U0VKMGVWSXJZV1ZtZHpacENpMHRMUzB0UlU1RUlGSlRRU0JRVWtsV1FWUkZJRXRGV1MwdExTMHRDZz09Cg==
Description: Base64 encoded K3s kubeconfig for cluster access
```

#### **Database Credentials**
```
MYSQL_USER: news_collector
MYSQL_PASSWORD: 99Rules!
MYSQL_ROOT_PASSWORD: 99Rules!
```

#### **Docker Registry**
```
DOCKER_USERNAME: <your-dockerhub-username>
DOCKER_PASSWORD: <your-dockerhub-token>
```

#### **Optional API Keys** (for enhanced functionality)
```
COINGECKO_API_KEY: <your-coingecko-api-key>
NEWSAPI_KEY: <your-newsapi-key>
REDIS_PASSWORD: (leave empty or set a password)
```

## Step 2: Create GitHub Environment

### 🎯 Environment Setup
1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name: `k3s-production`
4. Click **Configure environment**

### 🔐 Environment Protection (Optional)
- **Required reviewers**: Add yourself for deployment approvals
- **Wait timer**: Set to 0 minutes for immediate deployment
- **Deployment branches**: Limit to `main` branch

### 📋 Environment Secrets
Add these secrets to the `k3s-production` environment (same values as repository secrets):
- `K3S_KUBECONFIG`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

## Step 3: Test Repository Configuration

### 🔧 Quick Validation
1. Go to **Actions** tab in your repository
2. You should see these workflows available:
   - 🚀 Complete CI/CD Pipeline (KIND + K3s)
   - 🚀 K3s Production Deployment Pipeline
   - 🎯 Quick K3s Deploy

### 📊 Current Cluster Status
```
✅ K3s Cluster: 4 nodes (1 control-plane + 3 workers)
✅ Current Pods: 3 services running
   - enhanced-news-collector (worker3)
   - enhanced-crypto-prices-service x2 (worker2)
   - enhanced-onchain-collector (worker)
✅ External Access: http://172.18.0.4:30080
```

## Step 4: First Deployment Test

### 🚀 Option 1: Enhanced Complete CI/CD (Recommended)
1. Go to **Actions** → **🚀 Complete CI/CD Pipeline (KIND + K3s)**
2. Click **Run workflow**
3. Select:
   - **Use workflow from**: `Branch: dev`
   - **Deploy to K3s production cluster**: ✅ `true`
4. Click **Run workflow**

### 🎯 Option 2: Quick Deploy Test
1. Go to **Actions** → **🎯 Quick K3s Deploy**
2. Click **Run workflow**
3. Select:
   - **Deployment action**: `status`
4. Click **Run workflow**

### 📊 Option 3: Full K3s Pipeline
1. Go to **Actions** → **🚀 K3s Production Deployment Pipeline**
2. Click **Run workflow**
3. Configure options:
   - **Type of deployment**: `services-only`
   - **Force rebuild**: `false`
   - **Skip tests**: `false`
4. Click **Run workflow**

## Step 5: Monitor Deployment

### 📊 Monitoring Steps
1. **Watch Workflow**: Monitor the action in real-time
2. **Check Logs**: Click on failed steps to see detailed logs
3. **Verify Deployment**: Check the summary for service status

### 🔍 Local Verification Commands
```bash
# Check pod status
kubectl get pods -n crypto-core-production -o wide

# Check service status  
kubectl get services -n crypto-core-production

# Check recent events
kubectl get events -n crypto-core-production --sort-by='.firstTimestamp' | tail -20

# View deployment logs
kubectl logs -f deployment/enhanced-news-collector -n crypto-core-production
```

## 🎯 Expected Results

### ✅ Successful Deployment Should Show:
- **GitHub Actions**: All jobs green ✅
- **Pod Status**: All pods `Running` and `Ready`
- **Services**: All services have valid endpoints
- **External Access**: http://172.18.0.4:30080 accessible

### 🔧 Troubleshooting Common Issues:

#### **1. Kubeconfig Access Issues**
```bash
# Test locally first
kubectl cluster-info
# If this works, the GitHub secret should work too
```

#### **2. Pod Scheduling Issues**
```bash
# Check node taints and pod tolerations
kubectl describe nodes
kubectl describe pod <pod-name> -n crypto-core-production
```

#### **3. Image Pull Issues**
```bash
# Verify Docker credentials
docker login
# Check if images are accessible
docker pull python:3.11-slim
```

## 🎉 Next Steps After First Success

1. **Scale Services**: Test scaling with `kubectl scale`
2. **Add Monitoring**: Set up resource monitoring
3. **Enhance Deployments**: Add more of the 12 collectors
4. **Set up Alerts**: Configure deployment notifications
5. **Optimize Resources**: Fine-tune resource requests/limits

---

## 🚨 Emergency Commands

### Quick Rollback
```bash
# If something goes wrong
kubectl rollout undo deployment/<deployment-name> -n crypto-core-production
```

### Full Cleanup
```bash
# Remove all deployments
kubectl delete namespace crypto-core-production
kubectl delete namespace crypto-infrastructure
```

### Quick Status Check
```bash
# Overall cluster health
./scripts/deploy-to-k3s.sh status
```

---

**🎯 Your CI/CD pipeline is now ready for testing!** 

Start with the **Enhanced Complete CI/CD** option for the most comprehensive test. The pipeline will automatically detect your working K3s setup and deploy the services accordingly.