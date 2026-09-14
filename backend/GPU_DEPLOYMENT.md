# GPU inference deployment

The API server and GPU inference server run on separate EC2 instances in the
same VPC. Port 9000 on the GPU security group must accept traffic only from the
API server security group.

## GPU instance

```bash
cd /home/ubuntu/starton/backend
python3 -m venv .venv-gpu
source .venv-gpu/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-gpu.txt
cp .env.gpu.example .env.gpu
chmod 600 .env.gpu
```

Set `GPU_AI_API_KEY` to a random value of at least 32 characters and set the
adapter path in `.env.gpu`. Store the adapter and Hugging Face cache on the EBS
root volume, not on the ephemeral instance-store volume.

```bash
sudo cp deploy/starton-gpu.service /etc/systemd/system/starton-gpu.service
sudo systemctl daemon-reload
sudo systemctl enable --now starton-gpu.service
curl http://127.0.0.1:9000/health
sudo journalctl -u starton-gpu.service -f
```

## API instance

Use the GPU instance private IP and the same API key in `backend/.env`:

```dotenv
LOCAL_AI_ENABLED=true
LOCAL_AI_API_URL=http://GPU_PRIVATE_IP:9000
LOCAL_AI_API_KEY=the-same-random-secret
LOCAL_AI_TIMEOUT_SECONDS=120
```

Restart the API server after changing its environment:

```bash
sudo systemctl restart starton-backend.service
sudo journalctl -u starton-backend.service -f
```

Keep `LOCAL_AI_ENABLED=false` until the GPU health endpoint reports CUDA as
available. When the GPU instance is stopped, medical prompts fail closed and
non-medical prompts may use the configured Anthropic fallback.
