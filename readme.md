Built 1GB Server — a lightweight, production‑style monitoring service with a real‑time dashboard.
What it delivers:

Live CPU/RAM/Disk monitoring with updating charts (refreshing every 1s)
Health + metrics APIs for operational visibility
In-dashboard log capture + one‑click log download for quick troubleshooting/sharing
Clear App Footprint (RSS) reporting (the Python process memory in MB), separate from host usage

Why the “1GB” claim is credible (even if I developed on an 8GB machine):
the dashboard and health API expose the app’s own measured memory footprint (RSS) in real time  . The host may have more RAM available, but the application’s actual footprint is what determines whether it can run on a 1GB VPS.


#DevOps #CloudComputing #Python #Monitoring #SystemDesign #ResourceOptimization