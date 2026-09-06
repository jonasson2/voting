# Deploying the voting simulator

This guide runs the simulator as a durable Linux service:

```text
HTTPS reverse proxy → Waitress on 127.0.0.1:5000 → Flask application
```

systemd starts the service at boot and restarts it after failures. Waitress is
not exposed directly to the network.

## Prerequisites

- Linux with systemd
- Git and [uv](https://docs.astral.sh/uv/)
- A maintained Node.js LTS release with npm
- Either Caddy with a public DNS name, or an existing HTTPS nginx site

The examples use `/opt/voting`, an unprivileged `voting` account, and the
configuration files under `deploy/`.

## Install

Create the service account once, then clone and build as an administrator:

```sh
sudo useradd --system --home-dir /var/lib/voting \
  --shell /usr/sbin/nologin voting
sudo install -d -o "$USER" -g "$(id -gn)" /opt/voting
git clone https://github.com/jonasson2/voting.git /opt/voting
cd /opt/voting
uv sync --locked
cd vue-frontend
npm ci
npm run build-production
cd ..
```

Install and enable the systemd unit:

```sh
sudo install -o root -g root -m 0644 deploy/voting.service \
  /etc/systemd/system/voting.service
sudo systemctl daemon-reload
sudo systemctl enable --now voting
curl -I http://127.0.0.1:5000
```

The unit creates `/var/lib/voting` for writable simulation state. The deployed
source must be readable but not writable by the `voting` account.

If the checkout is not `/opt/voting`, update `WorkingDirectory` and `ExecStart`
in the unit before installing it. For a checkout under `/home`, also change
`ProtectHome=true` to `ProtectHome=read-only`; `/opt` is preferred.

The unit deliberately uses one Waitress process because active simulations are
stored in process memory. Its four request threads allow progress and download
requests while a simulation runs.

## Publish with HTTPS

Choose one reverse-proxy configuration. Keep Waitress bound to loopback and
allow public application traffic only through the proxy.

### Dedicated hostname with Caddy

Point the hostname's DNS record at the server and replace
`voting.example.com` in `deploy/Caddyfile`. Merge that site block into the
active Caddy configuration, then validate and reload it:

```sh
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Caddy obtains and renews the certificate automatically when ports 80 and 443
are reachable.

Verify the result:

```sh
curl -I https://voting.example.com/
```

### Path below an existing nginx hostname

The frontend supports a path such as `https://example.com/voting/`. Install the
location snippet:

```sh
sudo install -d -o root -g root -m 0755 /etc/nginx/snippets
sudo install -o root -g root -m 0644 deploy/nginx-voting-location.conf \
  /etc/nginx/snippets/voting.conf
```

Include it inside the existing TLS `server` block for the hostname:

```nginx
include /etc/nginx/snippets/voting.conf;
```

Validate, reload, and verify:

```sh
sudo nginx -t
sudo systemctl reload nginx
curl -I https://example.com/voting/
curl -I https://example.com/voting/static/js/bundle.js
```

The existing nginx server block must already have a valid certificate for the
hostname. Do not create a second port-443 block with the same `server_name`.

## Logs and service control

systemd records standard output and errors from both the web process and its
simulation subprocesses:

```sh
sudo systemctl status voting
sudo journalctl -u voting -f
sudo journalctl -u voting -n 100 --no-pager
sudo journalctl -u voting --since "today"
```

Control the service with:

```sh
sudo systemctl restart voting
sudo systemctl stop voting
sudo systemctl start voting
sudo systemctl disable --now voting
```

Restarting or stopping the service terminates active simulations.

## Update

Update only from a clean checkout and avoid restarting during active
simulations:

```sh
cd /opt/voting
git status --short
git pull --ff-only
uv sync --locked
cd vue-frontend
npm ci
npm run build-production
cd ..
sudo systemctl restart voting
```

Verify the internal service and public URL after each update.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `502 Bad Gateway` | Check `systemctl status voting` and `journalctl -u voting -n 100` |
| Public URL returns `404` | Confirm the proxy configuration is loaded in the correct hostname block |
| Blank or stale frontend | Rebuild with `npm run build-production`, then hard-refresh the browser |
| Service cannot read files | Check the unit paths, file permissions, and `ProtectHome` setting |

Always run the proxy's configuration test before reloading it. Confirm that
Waitress listens only on loopback with:

```sh
sudo ss -ltnp | grep ':5000'
```

## Security

- Serve the public application only through HTTPS.
- Keep Waitress on `127.0.0.1`; do not expose it directly.
- Keep the service unprivileged and its source tree read-only.
- Apply operating-system and dependency security updates.
- Add authentication, rate limiting, and suitable resource limits if the
  service is open to untrusted users; simulations can consume substantial CPU.
