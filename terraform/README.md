# Terraform: AWS VPC + EKS

This folder builds the AWS side of the project. Kubernetes only runs the workloads, something still has to create the network and the cluster, and that's what this does.

```text
VPC 10.30.0.0/16  (ap-south-1, 2 AZs)
 ├── public subnets   10.30.0.0/20, 10.30.16.0/20     -> NAT gateway, internet facing load balancers
 ├── private subnets  10.30.128.0/20, 10.30.144.0/20  -> worker nodes
 ├── 1 NAT gateway (single, to keep the bill down)
 └── EKS cluster clinicdesk-eks (Kubernetes 1.34)
       ├── managed node group: 2 x t3.medium (min 2, max 4), AL2023
       └── addons: coredns, kube-proxy, vpc-cni, pod identity agent, EBS CSI driver
```

I used the community `terraform-aws-modules` for the VPC and EKS instead of writing every resource by hand. The modules handle the route tables, IAM roles and security groups, which is a lot of boilerplate to get wrong.

## Files

| File | What's in it |
|---|---|
| `versions.tf` | Terraform and provider versions, commented out S3 backend |
| `providers.tf` | AWS provider with default tags on everything |
| `variables.tf` | All the knobs (region, sizes, versions, CIDR) |
| `main.tf` | VPC module, EKS module, IAM role for the EBS CSI driver |
| `outputs.tf` | Cluster name/endpoint, subnet IDs, the kubeconfig command |
| `terraform.tfvars.example` | Example values, copy to `terraform.tfvars` |

## Before you start

- AWS CLI configured (`aws configure` or `AWS_PROFILE`). No keys go in this folder.
- Terraform >= 1.7
- kubectl and helm

## Run it

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # edit if needed
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

Apply takes around 15 minutes, most of it is the EKS control plane.

Then point kubectl at the cluster:

```bash
$(terraform output -raw configure_kubectl)
kubectl get nodes
kubectl apply -f ../k8s/storageclass-gp3.yaml
```

The gp3 StorageClass is needed because EKS 1.30+ doesn't mark any StorageClass as default anymore, and without it the postgres PVC never binds.

## Tear it down

```bash
terraform destroy
```

Delete the Helm releases first (`helm uninstall clinicdesk -n clinicdesk` and the ingress controller). The ingress controller creates an AWS load balancer that Terraform doesn't know about, and if it's still there the VPC can't be deleted and destroy hangs on the subnets.

## Cost

Roughly what this costs in ap-south-1 while it's running:

- EKS control plane: $0.10/hour
- NAT gateway: about $0.056/hour plus data
- 2 x t3.medium: about $0.09/hour on demand (less on SPOT)
- load balancer from the ingress controller: about $0.025/hour

So a few dollars a day. Destroy it when you're done.

## Screenshots for submission

- [ ] `terraform plan` output: `docs/screenshots/terraform-plan.png` (TODO)
- [ ] AWS console VPC + EKS cluster: `docs/screenshots/aws-console-eks.png` (TODO)
- [ ] `terraform destroy` finished: `docs/screenshots/terraform-destroy.png` (TODO)
