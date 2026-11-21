# System & Network Architecture Documentation

## 1. Network Topology Architecture Diagram

The framework provisions an isolated virtual software-defined network using Linux Network Namespaces (`ip netns`) and Virtual Ethernet pairs (`veth`).

```
                              +---------------------------------------+
                              |         Client Host (ns_client)       |
                              |   10.0.1.2/24 (veth_c_p)              |
                              |   10.0.2.2/24 (veth_c_b)              |
                              |   Default Target: 10.50.0.1           |
                              +---------------------------------------+
                                  /                               \
               Primary Link      /                                 \   Backup Link
               veth_c_p <-> veth_p_c                     veth_c_b <-> veth_b_c
                                /                                   \
                               v                                     v
+------------------------------------------+     +------------------------------------------+
|       Primary Router (ns_primary)        |     |        Backup Router (ns_backup)         |
|   veth_p_c: 10.0.1.1/24 (Ingress)        |     |   veth_b_c: 10.0.2.1/24 (Ingress)        |
|   veth_p_s: 10.0.3.1/24 (Egress)         |     |   veth_b_s: 10.0.4.1/24 (Egress)         |
|   Routing Metric: 100 (High Priority)    |     |   Routing Metric: 200 (Standby Priority) |
|   net.ipv4.ip_forward = 1                |     |   net.ipv4.ip_forward = 1                |
+------------------------------------------+     +------------------------------------------+
                               \                                     /
               Primary Link      \                                 /   Backup Link
               veth_p_s <-> veth_s_p                     veth_b_s <-> veth_s_b
                                \                                 /
                                 v                               v
                              +---------------------------------------+
                              |      Destination Server (ns_server)   |
                              |   veth_s_p: 10.0.3.2/24               |
                              |   veth_s_b: 10.0.4.2/24               |
                              |   Loopback Service IP: 10.50.0.1/32   |
                              +---------------------------------------+
```

### Routing Table Configuration in Client (`ns_client`)

- **Primary Path (Baseline Active)**:
  `10.50.0.1 via 10.0.1.1 dev veth_c_p metric 100`
- **Backup Path (Standby)**:
  `10.50.0.1 via 10.0.2.1 dev veth_c_b metric 200`
- **Failover Active State**:
  `10.50.0.1 via 10.0.2.1 dev veth_c_b metric 50` (promoted by Failover Controller to override metric 100)

---

## 2. Module-Wise System Architecture

```
User (Web Browser)
        |
        v
+---------------------------------------------------------------------------------+
|                                 Flask Backend                                   |
|   [app.py] - REST API Endpoints & Template Rendering Controllers                |
+---------------------------------------------------------------------------------+
        |
        v
+---------------------------------------------------------------------------------+
|                           Network Testing Controller                            |
+---------------------------------------------------------------------------------+
     |           |                 |                 |              |          |
     v           v                 v                 v              v          v
+----------+ +-----------+ +---------------+ +-------------+ +----------+ +--------+
| Topology | | Monitoring| | Failure Engine| | Failover    | | Recovery | | Report |
| Manager  | | Engine    | | & Scenarios   | | & Failback  | | Analyzer | | Gen    |
+----------+ +-----------+ +---------------+ +-------------+ +----------+ +--------+
     |           |                 |                 |              |          |
     |           +---------[ Probe Stream ]--------->+              |          |
     |                                               |              |          |
     +-----------------------------------------------+              |          |
     |                                                              v          v
     |                                                       +----------------------+
     |                                                       |   Pandas Analytics   |
     |                                                       +----------------------+
     v                                                                  |
+-----------------------------------------------------------------------v----------+
|                                SQLite Database                                   |
|   sessions | probe_records | network_events | session_metrics                     |
+----------------------------------------------------------------------------------+
```

---

## 3. Linux Networking Commands & Operational Purpose

Every action performed by this framework invokes standard Linux `iproute2` and networking system utilities. Below is a comprehensive reference explaining each command:

### 1. Network Namespace Management
- `ip netns add <name>`: Creates a new isolated network namespace with its own network stack, interfaces, routing table, and ARP table.
- `ip netns del <name>`: Destroys a namespace, automatically deallocating its internal interfaces and assigned routes.
- `ip netns exec <name> <cmd>`: Executes arbitrary Linux commands inside the specified namespace's isolation boundary.

### 2. Interface Creation and Placement
- `ip link add veth_c_p type veth peer name veth_p_c`: Creates a bidirectional virtual Ethernet pair (`veth`). Packets entering `veth_c_p` immediately emerge from `veth_p_c`.
- `ip link set <dev> netns <ns>`: Moves one end of the veth pair into an isolated network namespace.
- `ip -n <ns> link set dev <dev> up`: Activates the network link operational state (`operstate UP`).
- `ip -n <ns> link set dev <dev> down`: Deactivates the network link (`operstate DOWN`), simulating link loss or unplugging a physical Ethernet cable.

### 3. IP Addressing
- `ip -n <ns> addr add <ip>/<cidr> dev <dev>`: Assigns an IPv4 address and subnet mask to the specified interface.
- `ip -n ns_server addr add 10.50.0.1/32 dev lo`: Binds a virtual service IP (`10.50.0.1`) to the loopback interface, reachable from any incoming interface.

### 4. IP Forwarding (Intermediate Routers)
- `ip netns exec <ns> sysctl -w net.ipv4.ip_forward=1`: Enables IPv4 kernel packet forwarding, allowing the namespace to route packets between its ingress and egress interfaces.
- `ip netns exec <ns> sysctl -w net.ipv4.ip_forward=0`: Disables IP packet forwarding, simulating a router freeze or gateway failure.

### 5. Routing Table Manipulation
- `ip -n <ns> route add <dest> via <gw> dev <dev> metric <metric>`: Installs a static route with an administrative priority metric.
- `ip -n <ns> route replace <dest> via <gw> dev <dev> metric 50`: Dynamically updates or promotes route priority to activate the backup path without restarting the application.
- `ip -n <ns> route del <dest> via <gw> dev <dev> metric <metric>`: Removes a route, simulating routing table corruption or route withdrawal.
- `ip -n <ns> route flush cache`: Clears the Linux kernel route lookup cache to ensure route changes take effect immediately.

### 6. ICMP Probing
- `ip netns exec ns_client ping -c 1 -W 1 10.50.0.1`: Sends a single ICMP Echo Request with a 1-second timeout to evaluate end-to-end reachability.
- `ip netns exec ns_client ping -c 1 -W 1 -I veth_c_b 10.50.0.1`: Sends an ICMP Echo Request bound specifically to the backup interface `veth_c_b` to verify backup path health prior to completing failover.
