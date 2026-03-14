import re

with open("/Users/pangjiade/Documents/GitHub/GCP-ESP/Document/conference_101719.tex", "r") as f:
    content = f.read()

replacement = r"""\subsection{Cloud-Native Principles}

From the old system architecture overview (Fig.~\ref{fig:arch1}), we can see that the previous iteration was a monolithic architecture suffering from single points of failure, lacking both scalability and resilience. To address these critical bottlenecks, we designed a new cloud-native microservices architecture (Fig.~\ref{fig:arch2}). This modernized design leverages several core cloud-native principles to ensure optimization for cloud environments.

Our architecture is inherently \textbf{Event-Driven} and employs \textbf{Asynchronous Messaging}. By utilizing Google Cloud Pub/Sub, we decouple data ingestion from processing, allowing the system to buffer messages during traffic spikes without data loss (at-least-once delivery guarantee). Furthermore, we implemented a \textbf{Streaming Data Pipeline} using Cloud Dataflow to process MQTT messages in real-time. Finally, resilience is heavily emphasized through \textbf{High Availability (HA)} mechanisms. The CloudNativePG operator manages a PostgreSQL cluster with automatic failover, while Kubernetes \textbf{Horizontal Pod Autoscaling (HPA)} dynamically adjusts our application replicas to maintain performance under variable loads.

\subsection{Component Rationale}
The selection of cloud components was driven by the necessity for a managed, scalable, and decoupled ecosystem. 
\begin{itemize}
    \item \textbf{Google Kubernetes Engine (GKE)}: Selected as the container orchestration platform for the gRPC server, PostgreSQL database, and observability stack. GKE abstracts control plane maintenance while seamlessly integrating with Google Cloud IAM.
    \item \textbf{Cloud Dataflow \& Pub/Sub}: Dataflow provides a serverless, auto-scaling Apache Beam runner to stream ETL workloads from the legacy MQTT broker into Pub/Sub. Pub/Sub acts as a resilient message broker that buffers high-throughput IoT streams before they are consumed by the internal application tier.
    \item \textbf{Compute Engine}: Hosts the Mosquitto MQTT broker on a Container-Optimized OS, acting as the crucial bridge for lightweight edge devices to interface safely with the cloud-native infrastructure.
\end{itemize}

\section{Technical Implementation \& Competency}
\subsection{Core Technologies}
The architecture is codified and deployed using \textbf{Terraform} (Infrastructure as Code), which handles the lifecycle of all GCP resources identically across environments. All workloads are fully containerized using multi-stage Docker builds to minimize attack surfaces and deployed alongside Kubernetes primitives (Deployments, Services, Secrets). Internal communications are facilitated via \textbf{gRPC} and \textbf{Protocol Buffers (protobuf)}, offering a highly efficient binary protocol compared to traditional REST APIs. Finally, real-time observability is achieved using \textbf{Prometheus} for infrastructure scraping and \textbf{Grafana} for unified dashboard visualization.

\subsection{Implementation Details}
The implementation strictly adheres to professional cloud-native practices. Security is enforced via the principle of least privilege, assigning explicit IAM service accounts (e.g., \texttt{dataflow.worker}, \texttt{pubsub.publisher}) to specific resources. Kubernetes Secrets are utilized to manage sensitive database and Grafana credentials rather than hardcoding. Performance is handled autonomously: the central gRPC consumer is configured via an HPA policy to scale from $2$ to $10$ pod replicas depending on a 60\% CPU utilization threshold. Additionally, the CloudNativePG operator maintains a primary and replica streaming database configuration, providing near-instant automatic failover to ensure zero downtime during node failures.

\subsection{Software Life Cycle \& Agile}"""

# Use regex to replace the specific block between "\subsection{Cloud-Native Principles}" and "\subsection{Software Life Cycle \& Agile}"
pattern = r"\\subsection\{Cloud-Native Principles\}.*?(?=\\subsection\{Software Life Cycle \\& Agile\})"
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open("/Users/pangjiade/Documents/GitHub/GCP-ESP/Document/conference_101719.tex", "w") as f:
    f.write(new_content)
