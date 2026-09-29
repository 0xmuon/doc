# Architecture from first principles

This is a study guide. It starts from the constraints that force software to have a shape, then walks through how those shapes were invented: machines, operating systems, networks, web applications, services, and FastAPI. SOLID sits in the middle because it is a set of rules for one of those shapes, the module, not a theory of the whole machine.

No document can name every architecture ever sold under a label. What follows is the family tree that explains the ones you will actually meet: layered systems, web apps, microservices, and the neighbors around them (event-driven systems, serverless, data pipelines, peer-to-peer, and the rest). Each section says what problem the idea solved, what it costs, and where the idea came from.

The shopping API in this repository is the running example. It is a layered monolith: one FastAPI process, one PostgreSQL process, Docker Compose in front of both. It is not a microservice system. The last section says exactly where it sits, so the history does not float free of the code.

References are numbered and collected at the end. The number is the source, not a decoration.

---

## 1. The constraints that come before any pattern

A program is a way of turning inputs into outputs over time, on a machine that forgets nothing unless you tell it to, fails when you did not plan for it, and sits a physical distance from the other machines it must talk to.

Five constraints show up in every architecture decision. They are older than the names we give the decisions.

**Time.** A CPU does one instruction stream per core. Waiting for a disk or a network is thousands to millions of times slower than a register. Architectures exist largely to decide who waits, and whether someone else can work during the wait.

**Space.** Memory is a hierarchy: registers, caches, RAM, disk, another machine. Copying data across a level costs more than computing on it where it already sits. Caching, batching, and "put the database next to the app" are space decisions.

**Failure.** Hardware, processes, and networks stop. A design either contains the blast (one request dies, the process lives) or spreads it (one shared database dies, every feature dies). Isolation is the architectural response to failure.

**Coordination.** Two actors who both change the same fact must agree on an order. Inside one process that agreement is a lock or a single thread. Across a network it is a protocol, a transaction, or an acceptance that the two sides will disagree for a while.

**Change.** Requirements move. The cost of a change is dominated by how many unrelated things you must touch. David Parnas wrote the durable version of this in 1972: decompose a system so that each module hides a decision that is likely to change [1]. That sentence is the root of layers, of SOLID, of services, and of "don't let the router talk to SQL."

Everything later in this guide is a particular answer to those five, under the tools of that decade.

---

## 2. How the shape of systems changed

Read this as a sequence of answers, each one keeping the previous machine and adding a boundary.

### One program, one machine (1940s–1950s)

The stored-program computer, written up in von Neumann's 1945 draft [2], put instructions and data in the same memory. Early jobs ran as a batch: load a deck, run to completion, print. There was no operating system in the modern sense. The program owned the machine. Architecture was the algorithm plus the wiring.

The pressure that broke this was wasted time. A job spent most of its life waiting on tape. People were expensive. The machine was expensive and idle.

### The operating system as a program that runs programs (1960s)

Time-sharing let many people use one machine by switching the CPU among them while one waited on I/O. CTSS at MIT and then Multics explored this. Unix, started at Bell Labs in 1969 by Ken Thompson and Dennis Ritchie, kept a much smaller idea and won: a process is a running program, a file is a stream of bytes, and programs talk by pipes [3] [4].

That is the first real architecture still in your laptop. The kernel is a layer under every process. User code cannot touch the disk or the network card directly. It asks, through a system call. The boundary exists so one program cannot destroy the others, and so the hardware decision is hidden behind a stable call. Parnas's rule, applied to the machine.

Dijkstra's THE multiprogramming system (1968) made the layering explicit: a stack of abstractions, each using only the one below [5]. Layered architecture in web apps is the same drawing, moved up from the OS into application code.

### Many machines, one conversation (1970s–1980s)

The ARPANET connected computers that did not share memory. The useful invention was not the cable. It was an address plus a protocol so that a program on one machine could name a program on another.

TCP/IP, designed by Vint Cerf and Bob Kahn and standardized at the end of the 1970s, became the ARPANET's protocol on 1 January 1983 [6] [7]. Berkeley's 4.2BSD (1983) put that stack into Unix with the sockets API. A socket is the file idea extended across a network: your process reads and writes bytes, and the kernel moves packets.

Client-server is the architecture that sockets made normal. One process listens. Another connects. The server holds the data. The client holds the screen. The 1980s and 1990s enterprise world then split the server again into an application tier and a database tier. That three-tier picture (presentation, domain logic, data) is still the picture of this shopping API, with the browser or Swagger as presentation, FastAPI as domain logic, and PostgreSQL as data.

### The web as a universal client (1990s)

In 1991 Tim Berners-Lee deployed HTTP, HTML, and URLs at CERN [8]. The architectural bet was extreme simplicity: a client sends a method and a path, the server returns a document, and the connection does not have to remember the conversation. Caching, proxies, and millions of anonymous clients fall out of that bet.

Roy Fielding, one of the authors of HTTP/1.1, wrote the dissertation that named the style REST (2000) [9]. REST is not "JSON over HTTP." It is a set of constraints: client-server, statelessness, cacheability, a uniform interface, and layering. This API is a JSON HTTP API in that tradition. It does not implement every REST constraint (it has no hypermedia controls in the responses), and it is honest to call it an HTTP API, not a pure REST system.

### Objects, components, and the modular monolith (1990s–2000s)

As programs outgrew one file, the industry tried larger bricks.

C++ and then Java made the class the unit people argued about. The Gang of Four book (1994) collected recurring class arrangements [10]. Bertrand Meyer stated the open-closed principle (1988) [11]. Barbara Liskov stated the substitution rule that keeps a hierarchy honest [12] [13]. Robert C. Martin collected a short list of module rules around 2000, and Michael Feathers later arranged five of them into the word SOLID [14] [15]. Section 5 goes through those five slowly.

At the scale of a whole business system, the style of the 2000s was often a modular monolith or a small set of tiers: one deployable application, packages inside it, one relational database. Fowler's *Patterns of Enterprise Application Architecture* (2002) catalogued what those systems kept reinventing: transaction script versus domain model, repository, unit of work, data mapper [16]. This shopping API is that tradition in Python: router, service, repository, SQLAlchemy models, one Postgres database, one deploy.

Service-oriented architecture (SOA) was the same decade's answer when the monolith crossed team boundaries. The idea was coarse services with explicit contracts, often XML and an enterprise bus. It solved ownership. It also produced heavy middleware. Microservices, named in a 2014 article by James Lewis and Martin Fowler [17], are SOA's smaller, independently deployable descendant, with the operational cost stated up front instead of hidden in a bus.

### Cloud, containers, and small deployables (2010s–2020s)

Amazon and others had already split large systems into services owned by teams. Conway's law (1968) is the social version: a system copies the communication structure of the organization that builds it [18]. Microservices make that copy deliberate. Each team ships its own process.

Docker (2013) made "a process plus its userspace" a packable artifact. Kubernetes, announced in 2014, schedules those artifacts across machines. Serverless platforms (AWS Lambda was launched in 2014) hide the process entirely: you upload a function, the platform runs it when an event arrives, and you pay for the run. A service mesh adds proxies beside services for retries, identity, and metrics. None of these change the five constraints. They move the boundary where you pay for them.

The 2020s reaction is visible and worth knowing. Many teams that split too early spent their time on network failures, distributed transactions, and deployment choreography. The modular monolith came back as a respectable choice: one deployable, hard module boundaries, the option to split a module out later. This repository is that choice on purpose. Week 3's later milestones add async, logging, and an external call inside the same process. They do not split the process.

---

## 3. Low-level systems, because the high-level picture sits on them

"Low level" here means the machine and the operating system, not a style of web framework. An API timeout, a blocked worker, and a Docker port mapping are all visible at this layer if you know what to look at.

### The processor and the memory hill

A core fetches an instruction, decodes it, executes it, and writes a result. That loop is the only kind of work the machine does. Everything else is waiting arranged around it.

Data lives at different distances:

| Store | Rough role | Why it matters to an API |
| --- | --- | --- |
| Registers | The CPU's own handful of values | Arithmetic happens here |
| Caches (L1, L2, L3) | Small, on or near the chip | A tight loop stays fast if its data fits |
| RAM | The process's working set | Your Python objects live here |
| Local disk | Durable, much slower | Postgres writes here; a commit waits on this |
| Another machine | Network round trip | Docker API to Postgres, or your laptop to the API |

A rule of thumb that has survived every hardware generation: do not cross a slower level inside a tight loop, and do not hold a worker idle across a slow level if other requests could run. ORMs, connection pools, and async I/O are three different attempts to obey that rule.

### The kernel boundary

The CPU has privilege levels. Kernel mode may talk to devices and to any memory. User mode may not. A **system call** is the controlled gate: your process puts a number and some arguments in registers and traps into the kernel. Open a file, read a socket, allocate memory, wait for a timer. Those are system calls.

This is why a Python web app cannot "just send a packet." It asks the kernel, through the runtime, through a library. The layering is: your function → CPython → the C library or a native extension → the kernel → the NIC or the disk.

An **interrupt** is the opposite direction. The device tells the CPU that something happened (a packet arrived, a disk finished). The kernel handles it and, if a process was waiting, marks that process runnable again. A blocked `recv` on a socket is a process asleep until a network interrupt wakes it.

**Virtual memory** gives each process the illusion of a private address space. The CPU's memory-management unit translates the process's addresses to physical frames. One process cannot read another's RAM by guessing an address. When this API and PostgreSQL run as two containers, they are two worlds of memory. They share data only by messages (the Postgres protocol over TCP), never by poking each other's objects. That isolation is the same idea as a microservice boundary, already present on your laptop between two processes.

### Processes, threads, and the Python runtime

A **process** is an address space plus one or more threads, file descriptors, and a user identity. A **thread** is a stack and an instruction pointer inside that address space. Threads in one process share objects. That is fast, and it is how a stray write corrupts another request's data if you are careless.

CPython, the interpreter this project uses, has a global interpreter lock around bytecode execution. Threads do not run Python bytecode truly in parallel on many cores. They do release the lock during many blocking I/O calls, so threads still help while a request waits on Postgres. The usual production pattern for CPU-bound Python is several processes, not several threads. Uvicorn, the server that runs FastAPI, can run workers as separate processes. This project's Compose file runs one API process with reload, which is the development shape, not a multi-worker production shape.

**Async**, which later milestones of this case study ask for, is a different trick inside one thread. A task runs until it awaits I/O, then the event loop runs another task. Nothing is waiting on the CPU during the database round trip. It is cooperative: a task that computes for a long time without awaiting blocks every other task on that loop. Async is a scheduling choice, not a speed charm.

### What "system software" means

System software is the layer that makes hardware usable by other programs and is not itself the user's job. The kernel, device drivers, filesystems, the C library, the language runtime, and in practice the database server all sit here.

PostgreSQL is system software from the application's point of view. It is a long-lived process. It owns files. It offers a protocol on a TCP port. It provides transactions so that "decrease stock and insert the order" either both happen or neither does. This API does not reimplement that. It sends SQL. Hiding SQL inside the repository is Parnas again: the decision "these rows live in Postgres, with these column names" can change without every route rewriting queries. In this code the decision has not been fully hidden (services know about sessions and domain rules), and that is a normal, readable split rather than a puzzle of abstractions.

Drivers and firmware matter to architecture only when they fail or when they define a limit (disk flush durability, NIC offload, clock drift). You do not design a shopping API around them. You do design it around the guarantees the OS and the database actually give you: a process can be killed at any instruction, a disk write is durable only after a successful flush, and two processes do not share objects.

---

## 4. Networks from the wire up

A network exists because two address spaces cannot see each other's memory. The substitute is a copy of some bytes, carried by a protocol that both sides already agreed to.

### Layers, as a teaching tool and as what actually runs

The OSI model (ISO 7498, 1984) stacks seven names: physical, data link, network, transport, session, presentation, application [19]. It is a vocabulary. The internet that runs is the TCP/IP family, which is thinner [6] [7]:

| TCP/IP piece | What it is responsible for | OSI name people map it to |
| --- | --- | --- |
| Link (Ethernet, Wi-Fi) | Frames on one local wire or radio | Data link |
| IP | Packets from one host address to another, across hops | Network |
| TCP or UDP | A conversation, or a single datagram, between ports | Transport |
| Your protocol (HTTP, the Postgres wire protocol) | Meaning of the bytes | Application |

IP does not know what a "login" is. TCP does not know what JSON is. HTTP does not know what a cart is. Each layer hides the one below. That is Dijkstra's layering [5] and the end-to-end argument of Saltzer, Reed, and Clark: functions such as reliability belong with the application that understands the data, not only in the middle of the network [20]. TCP gives you an ordered byte stream. Your API still has to decide what an order means.

### Addresses

An IPv4 address is 32 bits, written as four numbers from 0 to 255. It names an interface on a network, not a person and not a program. One machine can have several addresses (loopback, Ethernet, a Docker bridge, a VPN).

An IPv6 address is 128 bits. The loopback address there is `::1`, defined with the rest of the IPv6 address architecture [21].

Some addresses are reserved and must not be used as ordinary public hosts. The registry is IANA's special-purpose address list [22], summarized in RFC 6890 [23]:

| Block | Name | What a packet to it does |
| --- | --- | --- |
| `127.0.0.0/8` | Loopback | Stays inside this host. It is not forwarded. |
| `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | Private use (RFC 1918) [24] | Usable on a LAN or inside Docker. Not routable on the public internet. |
| `0.0.0.0/8` | "This network" | A special meaning in the IP rules, not a destination you browse to. |
| `169.254.0.0/16` | Link local | Self-assigned when DHCP fails. |

`/8` means the first 8 bits are fixed. `127.0.0.0/8` is every address from `127.0.0.0` through `127.255.255.255`, about 16 million addresses, all loopback.

### 127.0.0.1, its history, and what people confuse it with

IANA dates the reservation of `127.0.0.0/8` to September 1981 [22] [25]. That is the same month RFC 791 froze IPv4 [7]. The host rule that programmers actually rely on is RFC 1122 (October 1989), section 3.2.1.3: any address of the form `{ 127, <any> }` is an internal host loopback address, and a packet with such an address must not appear outside the host [26]. RFC 6890 repeats the block, marks it not forwardable and not globally reachable, and points back at that section [23].

So `127.0.0.1` is not a magic string invented by web frameworks. It is the conventional first address inside a block the internet standards reserved so a host could talk to itself. Most operating systems implement the whole block: `127.0.0.2` loops as well. The name people remember is `.1` because that is what the hosts file and the resolver were taught.

The name `localhost` is a separate invention from the number. It is a special-use DNS name. RFC 6761 says `localhost` resolves to a loopback address and should never be sent to the public DNS for a real answer [27]. On a current Windows or Linux machine, `localhost` often resolves to IPv6 `::1` first and to `127.0.0.1` second. If a server listens only on IPv4, a client that connects to `localhost` can hit the IPv6 address and fail, while `127.0.0.1` succeeds. This project's docs use `http://127.0.0.1:8000` for that reason.

What loopback actually does, mechanically: the kernel's network stack sees a destination in `127.0.0.0/8` and hands the packet back to a local socket. No Ethernet frame leaves the NIC. No router is involved. The packet still passes through enough of the stack that the port, the protocol, and the firewall rules apply. Loopback is not a function call. It is a network path of length zero.

Three addresses that get mixed up:

| You write | Meaning |
| --- | --- |
| `127.0.0.1` | This machine, IPv4 loopback. A server bound here accepts connections only from this machine. |
| `::1` | This machine, IPv6 loopback. |
| `localhost` | The name for loopback. Which number you get depends on the resolver order. |
| `0.0.0.0` | On a **bind**, "every IPv4 interface." Uvicorn in this project's container is started with `--host 0.0.0.0` so that port 8000 is reachable from outside the container, not only from inside it. `0.0.0.0` is not the address you type in a browser. You type `127.0.0.1` or the machine's LAN address. Connecting to `0.0.0.0` as if it were a peer is not how clients work. |

Docker adds one more twist. Inside Compose, the API reaches Postgres at the host name `db` and port `5432`. That name is registered on the Compose network, which is a private bridge. It is not `127.0.0.1`. From your laptop, `127.0.0.1` is your laptop, not the container's loopback. The laptop reaches Postgres through a published port: host port `5433` is mapped to container port `5432`. The number changes at the boundary. The process inside the database container still listens on 5432.

### Ports, from the beginning

A host address names a machine (an interface). Many programs run there. A **port** names the program's mailbox on that host, for a given transport protocol.

The idea is older than IP. On the ARPANET, the earlier protocol NCP already used socket numbers so one host could hold more than one conversation. TCP kept the idea and widened it. RFC 793 (September 1981) defines a TCP connection by a pair of endpoints, and each endpoint is an IP address plus a 16-bit port [28]. Sixteen bits means ports are integers from 0 to 65535. UDP has its own 16-bit port space. TCP port 80 and UDP port 80 are different mailboxes that happen to share a number.

A connection is five things, not one: protocol, source address, source port, destination address, destination port. That is why two browser tabs can both talk to `127.0.0.1:8000`. Each tab uses a different **ephemeral** source port. The server distinguishes the conversations by the full pair.

IANA divides the 16-bit space into three ranges. The procedure is RFC 6335 [29], and the practical advice is RFC 7605 [30]:

| Range | Also called | Who assigns it | How it is used |
| --- | --- | --- | --- |
| 0–1023 | System, or well-known | IANA, with a heavy review | HTTP 80, HTTPS 443, SSH 22, DNS 53, SMTP 25. On Unix, binding these historically required root, so an ordinary user could not pretend to be the system's web server. |
| 1024–49151 | User, or registered | IANA, on request | PostgreSQL 5432, MySQL 3306, and many application servers. Any user may bind one if it is free. |
| 49152–65535 | Dynamic, private, or ephemeral | Nobody. Never assigned. | The OS picks these as temporary source ports for outgoing connections. |

"Registered" is a messy word. RFC 7605 points out that people use it both for 1024–49151 and for everything IANA has written down, including well-known ports [30]. When you read a table, check which range it means.

A server **listens** on a port. A client **connects** to that port from an ephemeral port. The well-known number is a convention so the client does not have to ask, "which port is HTTP today?" The convention for the web is 80 for cleartext HTTP and 443 for TLS, recorded in the HTTP specifications [31]. Port 8000 is not that convention. It is a long-standing development habit (Django's development server and Uvicorn both default near it). This API publishes 8000 because that is the development choice in the Compose file, not because IANA assigned shopping APIs to 8000. PostgreSQL's registered port is 5432. This project publishes **5433** on the laptop so it does not collide with a Postgres the laptop might already be running on 5432. Inside the Compose network the database is still 5432.

Port 0 is reserved. Asking the OS to bind port 0 usually means "give me any free ephemeral port," which is a testing trick, not a public address.

### TCP in one page

UDP sends a datagram and does not promise that it arrives, or that two datagrams arrive in order. DNS queries often use UDP because one small question and one small answer do not need a conversation.

TCP builds a reliable, ordered byte stream on top of IP, which itself does not promise those things [28]:

1. **Handshake.** The client sends SYN. The server replies SYN-ACK. The client sends ACK. Both sides now have sequence numbers. This is three messages before your HTTP request exists.
2. **Data.** Each side sends bytes and acknowledges the sequence numbers it has received. Lost segments are resent. The application sees a stream, not packets.
3. **Close.** Each side sends FIN and acknowledges the other. A connection has a life. A half-closed connection is a real state, which is why "the client went away" shows up in servers as a specific error rather than silence.

HTTP/1.0 often opened a TCP connection per request. HTTP/1.1 kept the connection open for more requests (keep-alive) because the handshake and slow-start were expensive [31]. HTTP/2 multiplexes many streams on one connection. HTTP/3 replaces the TCP under HTTP with QUIC over UDP, because TCP's "one lost packet stalls the whole stream" hurt multiplexed HTTP. You can serve this API without caring, until a proxy or a load balancer in front of it does care. Uvicorn speaks HTTP/1.1 to whatever calls `127.0.0.1:8000`.

TLS sits between TCP and HTTP on port 443. It gives confidentiality, integrity, and a server identity. This development API does not use TLS. A production deployment in front of a real network would terminate TLS at a proxy or at the platform, not by inventing cryptography inside a route.

### DNS, very briefly

People type names. Packets need numbers. DNS is the distributed lookup. For `localhost`, the lookup is specified to stay local [27]. For `db` inside Compose, the lookup stays on Docker's internal resolver. For a public name, the lookup walks from a recursive resolver toward an authoritative server. Caching is part of the design: a name can keep pointing at an old address until the TTL expires. That is why deployments treat DNS delay as a real failure mode, not as a detail.

### The fallacies that show up the moment you leave loopback

Peter Deutsch and colleagues at Sun wrote down the assumptions engineers keep making once a call crosses a network. The usual list: the network is reliable, latency is zero, bandwidth is infinite, the network is secure, topology does not change, there is one administrator, transport cost is zero, the network is homogeneous [32]. Loopback almost makes the first few feel true, which is why a feature that works against `127.0.0.1` still needs timeouts and retries when the same call goes to a payment service on another host. Milestone 4 of the case study (external calls with timeout and retry) is this list turned into code. It is not part of the current API.

---

## 5. SOLID, from the module outward

SOLID is a mnemonic for five rules about modules. Robert C. Martin wrote the underlying principles up around 2000 as advice against software rot, in "Design Principles and Design Patterns," and at book length in *Agile Software Development, Principles, Patterns, and Practices* (2002) [14] [33]. Michael Feathers arranged five of them into the acronym SOLID around 2004. That attribution is the standard secondary account (Martin credits Feathers for the name); it is not a paper by Feathers with the word in the title [15].

The letters are not one theory discovered on one day. Two of them are older than Martin, and they were answers to different problems.

| Letter | Principle | First published form |
| --- | --- | --- |
| S | Single responsibility | Martin, early 2000s. His later wording is "a module should be responsible to one actor" [34]. |
| O | Open-closed | Bertrand Meyer, *Object-Oriented Software Construction* (1988): open for extension, closed for modification [11]. |
| L | Liskov substitution | Barbara Liskov, "Data Abstraction and Hierarchy" (1987), then the subtype relation with Jeannette Wing (1994) [12] [13]. |
| I | Interface segregation | Martin, late 1990s: clients should not depend on methods they do not use [14]. |
| D | Dependency inversion | Martin, late 1990s: high-level policy depends on abstractions, not on low-level details [14]. |

They can conflict. A class split until every method is its own type satisfies a cartoon of S and I and becomes impossible to read. The aim is the cost of change, not a score.

### S — one reason to change

The early wording was "one responsibility." The useful wording is narrower: one actor who can ask for a change. A module that calculates order totals and also formats HTTP errors changes when finance changes the rounding rule and when the API team changes the error JSON. Those are two actors. Split them if both change often. Leave them if the same person owns both and they change together.

In this API the split already follows actors:

| Module | Actor who causes it to change |
| --- | --- |
| `app/schemas` | The contract of the JSON. A field rename. |
| `app/services` | The shop rule. Stock, checkout, "one open cart." |
| `app/repositories` | The query shape. |
| `app/models` | The table shape. |
| `app/routers` | The URL and the status code. |
| `app/utils/security.py` | The token format. |

A checkout rule does not belong in the router. A status code does not belong in the repository. That is S applied to a layered app, and it is why the case study insists on the layers.

### O — add behavior without editing the stable core

Meyer's original setting was a published library: once others inherit from your class, you should add behavior by new types, not by editing the base and breaking them [11]. In a small application you control every caller, so "closed for modification" is often the wrong religion. Editing `login_user` to issue a JWT was the right change for milestone 1. The open-closed move is reserved for variation you can already name.

The planned milestone 2 policy map is the open-closed move in this project. Routes would ask for a permission. A new role would be a new entry in the map, not a new `if` inside every route. The routes stay closed. The map stays open. Until that map exists, role checks are not in the code, and pretending otherwise would be the principle without the mechanism.

### L — a substitute must keep the promises

Liskov's rule is about behavior, not about sharing method names. If a function accepts a `User`, any stand-in must honor the properties the function relies on: an id, a stored password hash, the ability to own a cart. A type that throws on `email` where `User` would return a string is not a substitute, even if the method exists.

The 1994 paper with Wing makes this a contract on subtype relations [13]. The failure mode in real code is a subclass that overrides a method and weakens a guarantee ("this save sometimes does not save"). Callers that were correct for the base type become wrong. In a language with duck typing, the same bug appears without inheritance: a test double that returns `None` where the repository returns a model.

### I — do not force a caller to depend on the whole buffet

A fat interface couples every client to every change. The SQLAlchemy `Session` is already a wide interface. This code does not pass the session into the JWT helper, and the JWT helper does not accept a session. `create_access_token` takes a user id and an email. That small signature is interface segregation at function scale. `get_current_user` is the wide door for routes that truly need the row.

The symptom of ignoring I is a function with eight parameters, three of which every caller passes as `None`.

### D — the policy names an abstraction, the detail plugs in

Dependency inversion is the structural rule. High-level policy (checkout) should not be wired by hand to a concrete low-level mechanism (a particular SQL string, a particular clock, a particular HTTP client) if that mechanism is what varies. Both should depend on a small idea in the middle ("a cart repository," "a clock," "a payment client").

This API inverts one dependency for real: routes ask FastAPI for a `Session` through `Depends(get_db)`, and services call repository functions. The router does not construct the database engine. A second inversion is only partial, and that is acceptable at this size: repository functions are concrete modules, not interfaces with swappable classes. Python lets you patch a module in tests later. Building a class hierarchy of repositories now would add types and hide no decision that is actually changing.

Martin's Clean Architecture book (2017) draws the same rule as concentric circles: entities inside, use cases around them, interface adapters around those, frameworks and databases on the outside [34]. The dependency arrows point inward. Hexagonal architecture, which Alistair Cockburn described in 2005, is the same arrow: the application is the hexagon, and the database and the web are adapters at the ports [35]. This repository is a light version. FastAPI and PostgreSQL are both outside the service rules. The services do import SQLAlchemy sessions, so the circle is not pure. Purity would mean the service never sees a `Session`. The gain at that point is smaller than the indirection, until a second database or a serious test suite forces the issue. Milestone 6 is the test suite. It is not written yet.

### What SOLID does not decide

SOLID does not choose microservices, a message bus, or a cloud. It does not make code fast. A single-responsibility function can still call the database in a loop. It does not replace transactions, indexes, or an honest schema. It is a module rule. Use it when a change keeps hurting unrelated code. Ignore a letter when obeying it would split a stable concept into pieces nobody can hold in their head.

---

## 6. The architectures you will hear named

Think of these as answers to "where is the boundary?" The boundary is always one of the five constraints from section 1. The names overlap. People sell the same drawing under two titles.

### Layered (n-tier)

Dijkstra's stack, moved into business software [5]. Presentation calls domain logic. Domain logic calls data access. Data access calls the database. A layer may use the layer directly under it and not the one above it.

This project is four layers plus a database:

`router → service → repository → model`, and the model is mapped onto PostgreSQL.

The gain is the direction of change. The cost is a feature that needs a new column touching every layer, which is the right cost if you want each concern reviewed in its own file. Strict layering forbids a shortcut from the router to the model. This code mostly holds that line.

Three-tier is the deployment view of the same idea: browser, application server, database server. They can be three processes even when the application code is one codebase. That is this Compose file.

### Modular monolith

One deployable process, several modules, rules about who may import whom. The database is usually shared, with tables owned by modules by convention. You get one transaction across "cart" and "order," which a microservice split would turn into a distributed transaction. You pay by being unable to scale or redeploy one module alone.

For a single team and a single shop, this is the production-shaped default. Splitting is a later response to a measured limit or to a team boundary, not a starting style.

### Microservices

A microservice is a small service with its own deployable process, its own data, and a network API, owned by a team that can release it without releasing the others [17]. The architectural gain is independent change and failure isolation. The costs, which the 2014 article already listed, are operational: distributed data, no cross-service join, eventual consistency, versioned contracts, observability, and the fallacies of section 4.

A shopping system split by force of habit might become users, catalog, cart, orders, payments. Each would have a database. Checkout would stop being one SQL transaction and become a saga: a sequence of local transactions with a compensating action when a later step fails. That is a real architecture. It is the wrong one while one person can still hold the whole schema and one Postgres commit can still decrement stock and insert the order together. This API keeps that single commit on purpose.

Related words, and what they add:

| Name | The extra idea |
| --- | --- |
| SOA | Coarse services, often a shared bus, the 2000s predecessor. |
| Nanoservice | A service so small that the network hop costs more than the work. Usually a warning, not a goal. |
| Service mesh | Sidecar proxies (identity, retry, metrics) so application code does not reimplement them. |
| API gateway | One front door that authenticates, routes, and rate-limits before traffic hits services. |
| Backend for frontend | A gateway shaped for one client (the mobile app, the web app), so clients do not each call ten services. |
| Strangler fig | Grow the new system around the old one, route by route, until the old one can be removed. A migration plan, not a runtime style. |

### Hexagonal, onion, and clean

Three drawings of one rule: the domain does not import the framework [34] [35].

- **Hexagonal (ports and adapters).** The application exposes ports. An HTTP adapter and a database adapter plug in.
- **Onion.** Circles. The domain is the center. Infrastructure is the outer ring.
- **Clean.** Martin's version of the circles, with an explicit "use case" ring.

Use the vocabulary with your team if it helps the dependency arrow stay inward. Do not build the ceremony (interfaces for every repository, mappers for every row) until a second adapter exists. The second adapter is what makes the port earn its keep.

### Client-server and peer-to-peer

Client-server: an asymmetric pair. The server listens, holds the shared state, and outlives any one client. This API is a server. Swagger, curl, and a future mobile app are clients.

Peer-to-peer: nodes are symmetric. BitTorrent and some blockchains are the famous cases. A shopping API is a poor peer-to-peer system because the stock count is a single fact that must have an authority. If every client held a copy of stock, you would have invented a consensus protocol to answer "who may buy the last lamp?"

### Event-driven, brokers, and streaming

Instead of "call me and wait," a component publishes a fact ("order placed") and others react. A broker (a queue or a log) stores the fact until consumers take it. The gain is decoupling in time: the email sender can be down when checkout succeeds, and can catch up later. The cost is that the user did not get a single synchronous answer, and you must handle duplicates. Consumers see the same message twice, so the work has to be safe to repeat.

Event sourcing stores the events as the source of truth and rebuilds current state by replay. CQRS splits the write model from the read model so each can be shaped for its job. Both are powerful when the history of changes is the business (audit, finance) and expensive when a row with a status column would do. This shop stores current carts and orders as rows. It does not store a log of every quantity change. That is a deliberate simpler model.

### Actor systems

An actor owns its state and its mailbox. It processes one message at a time. Other actors never touch its memory. Erlang/OTP made this the structure of a whole system, supervision trees included. It is a low-level answer to coordination: isolate state, serialize access. A database row with a transaction is the boring version of the same isolation for this shop.

### Data architectures

These decide how facts are stored and copied, not how HTTP is shaped.

| Name | Idea |
| --- | --- |
| Relational (this project) | Tables, keys, transactions. One current truth. PostgreSQL. |
| Document store | One aggregate as one document. Fewer joins, weaker cross-document constraints. |
| Key-value | A fast map. Sessions and caches. Not a catalog with relations. |
| Columnar / warehouse | Data laid out for scans and aggregates, usually a copy of the operational store, not the store that takes the order. |
| Lambda architecture | A batch path and a speed path, merged into views. Nathan Marz's answer to "big data" around 2011. Heavy. |
| Kappa architecture | Jay Kreps's counter: keep one log, reprocess it, drop the separate batch path. |
| Data mesh | Zhamak Dehghani's organizational answer: domains own their analytical data as products, instead of one central lake team owning everything. |

OLTP versus OLAP is the old cut. This API is OLTP: short transactions, current stock, current carts. A sales report over years of orders wants a different shape and should be a copy, not a heavy query on the checkout database.

### Workflow and consistency patterns

When one database transaction is not enough, these are the named tools:

- **Saga.** A sequence of local transactions, each with a compensation if a later step fails. The alternative to a distributed two-phase commit, which locks across services and fails badly under partial outages.
- **Outbox.** Write the business row and the "please publish this event" row in the same database transaction. A separate publisher reads the outbox. You do not lose the event if the process dies after the commit and before the network call.
- **Idempotency key.** The client sends a key. A retry of checkout does not create a second order.
- **Circuit breaker.** After N failures, stop calling the sick dependency for a while. Michael Nygard's *Release It!* is the usual source for this family of stability patterns [36].

Milestone 4's retry and timeout are the small version. A circuit breaker is the next step if the external service can stay sick and drown the API in waiting.

### Runtime platforms, which are not architectures by themselves

| Platform | What it actually gives you |
| --- | --- |
| Virtual machine | An isolated fake computer. Heavy, familiar, strong separation. |
| Container | An isolated process tree with its own filesystem view, sharing the host kernel. This project's Docker image. |
| Orchestrator | Schedules containers, restarts them, gives them a network. Kubernetes is the common one. Compose is the small one, and it is what this repo uses. |
| Serverless function | Run this callable on an event, scale to zero, a hard time limit, awkward long connections such as database pools. |
| PaaS | Someone else's process supervisor plus a buildpack. |

Choosing Docker does not mean you chose microservices. This repo runs two containers because the API and the database are already two processes. That is client-server, packaged.

### UI architectures, for when a front end appears

This repository has no UI. The names still come up.

| Name | Where the state and the rendering live |
| --- | --- |
| MVC | Model holds state, view renders, controller takes input. Smalltalk, then the web, with many incompatible meanings of "controller." |
| MVP | The presenter is the middle, the view is passive. Common in older desktop UI. |
| MVVM | A view-model shaped for binding. Common in rich clients. |
| SPA | The browser holds a long-lived client and calls an HTTP API. This API is built to be that API. |
| SSR | The server renders HTML per request. A different front door on the same domain rules. |

The domain rules belong on the server either way. A browser that is the only place stock is checked will be wrong the moment a second client exists.

### A map from constraint to usual answer

| If the pain is… | The architecture people reach for |
| --- | --- |
| One file knows too much | Layers, SOLID, a module boundary |
| Two teams cannot release together | A service boundary, a modular monolith first if the teams are still small |
| A call must survive the callee being down | A queue, an outbox, a retry with a timeout |
| The same data is read in a shape that fights the write shape | A read model, CQRS, a warehouse copy |
| One machine is out of CPU or RAM | A bigger machine first, then more processes, then a split |
| One bug must not be allowed to read another customer's memory | A process boundary, and authorization inside the process. This API already has the second. |

---

## 7. Web applications, as a specific architecture

A web application is client-server where the conversation is HTTP and the client is often not yours. That last fact dominates the design. You do not control the browser, the mobile app, or the person calling curl. Any rule that matters (price, stock, who owns the cart) has to be enforced on the server. The client is a convenience.

### How a request used to be served

**CGI** (Common Gateway Interface, around 1993) started a new operating-system process for each HTTP request and passed the request on standard input and environment variables. Isolation was excellent. Startup cost was terrible.

Servers then learned to keep the application loaded. **WSGI** (PEP 333, 2003, Phillip Eby) standardized the Python version of that: a server calls a Python function with an environment dictionary and a start-response callback [37]. One process serves many requests. Django (2005) and Flask (2010) are WSGI applications. The function returns when the response is ready. If the function waits on a database, that worker waits.

**ASGI** is the async successor, started by Andrew Godwin in 2016 so Django Channels could speak WebSockets as well as HTTP, and cleaned up into the single-callable ASGI 3.0 spec in 2019 [38] [39]. A server calls an application with a scope, a receive channel, and a send channel. The application is a coroutine. It can await. Section 8 follows that into FastAPI.

### HTTP itself

HTTP/0.9 was a GET and a document. HTTP/1.0 added headers and status codes. HTTP/1.1 added persistent connections, chunked bodies, and the host header so many sites could share an IP [31]. HTTP/2 added binary framing and multiplexed streams. HTTP/3 runs those streams over QUIC.

Methods carry intent: GET reads and should be safe to repeat, PUT replaces, POST submits a process, DELETE removes. This API uses those meanings: GET for catalog and cart reads, POST for register, login, add-to-cart, and checkout, PUT to set a quantity, DELETE to drop a line. Checkout is POST because it is a process (prices are copied, stock moves, the cart closes), not because POST is the method people use when they are unsure.

Status codes are the small contract:

| Code | Contract in this API |
| --- | --- |
| 200 | The read or the update happened. Login is 200. |
| 201 | A new row or a new order exists. |
| 400 | The shop rule refused (stock, empty cart). |
| 401 | We do not know who you are. |
| 403 | We know who you are, and this is not yours. |
| 404 | That row is not there. |
| 409 | The unique rule failed (duplicate email). |
| 422 | The body failed the schema. |
| 500 | The server failed in a way the route did not translate. The handler hides the internal text. |

### State, sessions, and tokens

HTTP is stateless in Fielding's sense: each request carries what the server needs, and the server does not keep a conversational memory keyed only by "the same TCP connection" [9]. Applications still need to know who is calling.

The old answer is a session: the server stores a row, the client stores a random id in a cookie, and every request presents the cookie. The server looks the row up. Logout deletes the row. This is easy to revoke and annoying to share across many servers unless the session store is shared.

The answer this API uses is a **JWT**: a signed set of claims (`sub`, `email`, `exp`), defined by RFC 7519 [40]. The server does not store the token. Any server that has the same secret can check the signature. The cost, which milestone 2's plan states directly, is revocation. A token stays valid until `exp` unless the server checks a fact the token does not own. Loading the user from the database on each protected call, which `get_current_user` already does, means a deleted user loses access immediately. A role that lived only inside the token would not.

Passwords are not a network topic, but they sit on the same request. This API stores PBKDF2-HMAC-SHA256 as `salt$hex` and never returns the hash. Login returns one error for a bad email and a bad password so a caller cannot use the message as an account oracle.

### OpenAPI

OpenAPI is a description of an HTTP API. FastAPI builds it from the type annotations and serves Swagger UI at `/docs`. The document is generated from the code, so the code remains the source of truth. A hand-written spec that drifts from the routes is a second system to maintain. For a public API with several client teams, a reviewed spec is sometimes the contract and the code is checked against it. This project is in the first mode.

---

## 8. FastAPI, and the line of tools it stands on

### The line

| Year | Piece | Why it exists |
| --- | --- | --- |
| 1993 | CGI | Run a program per request. |
| 2003 | WSGI, PEP 333 [37] | One Python process, many requests, servers and frameworks interchangeable. |
| 2005 | Django | A full framework: ORM, admin, templates, the "batteries" monolith. |
| 2008 | SQLAlchemy 0.5 era already mature; the 1.4/2.0 style this project uses is much later | A data mapper so Python objects are not secretly the SQL driver. |
| 2010 | Flask | A small WSGI core. Extensions add the rest. |
| 2014 | Python 3.4 asyncio (PEP 3156) | An event loop in the standard library. |
| 2015 | Python 3.5 async/await (PEP 492) | Syntax that makes the loop readable. |
| 2014–2016 | PEP 484 and PEP 526 type hints | Annotations a library can read at runtime, not only a checker. |
| 2016 | ASGI proposed by Andrew Godwin for Django Channels [38] | HTTP and WebSockets, async, a new calling convention rather than a fork called "WSGI 2." |
| 2017–2018 | Uvicorn (Encode, Tom Christie) | A fast ASGI server, built on uvloop and an HTTP parser. |
| 2018 | Starlette (Encode) | A small ASGI toolkit: routing, requests, responses, middleware, websockets. |
| 2018-12-05 | FastAPI 0.1.0, Sebastián Ramírez [41] [42] | Starlette for the web, Pydantic for the data, type hints as the syntax, OpenAPI as a byproduct. |
| 2019-03 | ASGI 3.0 [39] | The application becomes a single async callable. |
| 2019 | Ramírez's introduction post [43] | He describes years of trying to assemble the same features from existing frameworks before writing a new one. APIStar, Flask, and Django REST are the neighborhood he was working in. |
| 2023 | FastAPI 0.100 line | Pydantic v2 becomes the validation stack the framework is built around. Models, serializers, and a large amount of application code had to move. This project is on that side of the break (`field_validator`, `model_validate`). |

The current release line has kept moving well past 0.100. Treat the GitHub releases page as the list of record for the exact latest number [44]. Pinning a "latest version" in a study guide is how a document goes stale.

FastAPI's own description of its base has been stable since the beginning: Starlette for the web parts, Pydantic for the data parts [43]. Performance claims in the early material pointed at TechEmpower benchmarks of a Uvicorn plus Starlette stack, and they are benchmarks of a particular test, not a promise about a route that talks to Postgres. In this API the database round trip dominates. The framework's speed is not the bottleneck.

### What happens when a request hits this API

1. The client opens TCP to `127.0.0.1` port `8000` (or, from another container, to the API container's address on port 8000).
2. Uvicorn accepts the connection, reads HTTP, and calls the ASGI application.
3. FastAPI is a Starlette application. Middleware runs first. This app installs CORS middleware that allows any origin, which is a development setting, not a locked-down browser policy.
4. Routing matches the method and the path. `/products/search` is registered before `/products/{product_id}` so the word `search` is not captured as an id.
5. Pydantic validates the body, the path, and the query against the schema. Failure becomes **422** before your function runs.
6. Dependencies run. `get_db` opens a SQLAlchemy session for the request and closes it afterward. On cart and order routes, `get_current_user` reads the bearer token, checks the signature and the expiry, and loads the `Users` row.
7. The route function runs. It should stay thin. It calls a service.
8. The service applies shop rules and calls repositories. A business failure raises `AppException`. The handler in `main.py` turns that into `{"detail": "..."}` with the status code on the exception. Anything else becomes a logged **500** with a generic body.
9. The return value is filtered through the response model. A `User` row becomes a `UserResponse`. The password hash has no field, so it cannot leak by accident.
10. Uvicorn writes the HTTP response. The session is closed. The TCP connection may stay open for another request.

That path is the whole architecture of the process. There is no queue, no second service, and no background worker in the current code.

### Why the pieces are separate libraries

If FastAPI had implemented HTTP, validation, and OpenAPI itself, a change in any of them would be a framework release, and none of them could be used alone. Starlette is usable without FastAPI. Pydantic is usable without either. Uvicorn will run any ASGI app. The framework is a composition, which is dependency inversion at the ecosystem scale: FastAPI depends on those libraries' public contracts.

The cost of composition is version coupling. A Pydantic major release forced a FastAPI major line (the 0.100 work). When you read a traceback, identify which layer raised it before editing a route. A validation error is Pydantic. A connection refused to `db:5432` is the network and Postgres, not a schema bug. A 401 is `get_current_user`.

### Sync today, async as a later choice

The routes in this repository are ordinary `def` functions. FastAPI runs those in a threadpool so a blocking SQLAlchemy call does not freeze the event loop. That is a sound default for a sync ORM.

An `async def` route runs on the event loop. It must not call a blocking database driver directly, or it stalls every other request on that loop. Milestone 5 of the case study asks for a deliberate conversion of one flow, an async session, and a background task, plus a written reason. The reason belongs in the five constraints: use async where the work is waiting on I/O and many waits can overlap; keep sync where the code is simpler and the database driver is the blocking one you already understand. Async is not more correct. It is a different way to spend the wait.

---

## 9. Distributed systems, only as far as this shop will need them

You already run a distributed system of two processes. The API can be up while Postgres is down. The request then fails. That is the smallest distributed failure, and the code should turn it into a **500** rather than a partial order. A single SQL transaction around checkout is what prevents "stock decreased, order missing."

The moment a third system appears (a payment gateway, milestone 4), the transaction cannot cover it. The durable approach is: commit the order in a state that means "payment not finished," call the gateway with a timeout, retry with a limit, and record the outcome. If the process dies after the gateway charged the card and before you stored the result, a retry must not charge twice. That is an idempotency key on the gateway, or a lookup-by-order before charging again. The outbox pattern is the same idea if the call is replaced by a message.

**CAP**, stated by Eric Brewer in 2000 and proved in a narrow form by Gilbert and Lynch in 2002, says that under a network partition a distributed store cannot be both perfectly consistent and perfectly available [45] [46]. The useful reading is not the slogan. It is: when the link between two copies fails, you either refuse writes (consistency) or you accept writes that will conflict (availability). PACELC, Daniel Abadi's extension, adds the twin question for when the system is healthy: latency versus consistency [47]. Postgres in one box does not force you to choose. Two Postgres servers with replication do.

Consistency words you will meet:

| Word | Meaning |
| --- | --- |
| Strong, linearizable | A read sees the latest completed write. One node Postgres gives you this. |
| Read-your-writes | A client at least sees its own update. Sessions and "read from the primary" aim here. |
| Eventual | If updates stop, copies agree. They may disagree now. DNS and many caches. |
| Causal | You at least do not see an effect before its cause. |

This API wants strong consistency for stock. Two checkouts must not both buy the last unit. The database transaction and the quantity check are that decision. A cache of product lists could be eventual. A cache of stock counts, used as the authority at checkout, would be a bug.

---

## 10. Where this repository sits

| Question | Answer in this repo |
| --- | --- |
| Machine architecture | Two processes on one kernel, packaged as containers. |
| System software underneath | Linux in the images, CPython 3.12, PostgreSQL 17. |
| Application architecture | Layered modular monolith. |
| Web style | HTTP JSON API, OpenAPI generated, not a rendered site. |
| Auth | Stateless JWT after a database password check. Protected cart and orders. |
| Data | One relational database, foreign keys, one transaction for checkout. |
| Network | Loopback from the laptop to published ports. A private Docker network between API and database. |
| Not chosen | Microservices, a message broker, CQRS, event sourcing, TLS, a public gateway, async routes. |

The directory is the layer diagram:

| Path | Role in the history above |
| --- | --- |
| `app/routers` | HTTP adapter. Paths, status codes, dependencies. |
| `app/schemas` | The contract. Pydantic. |
| `app/services` | The use cases. Shop rules. |
| `app/repositories` | The persistence adapter, still concrete. |
| `app/models` | The relational shape. |
| `app/db` | Session, engine, seed. The engine is infrastructure. |
| `app/utils/security.py` | Token detail, hidden from the routes. |
| `app/utils/deps.py` | The reusable gate. Milestone 1's version of "one place for the check." |
| `Dockerfile`, `docker-compose.yml` | The 2010s packaging of the two-process system. |

A request you can trace by hand, and the layers it crosses:

`POST /api/orders/checkout` with a bearer token → Uvicorn → CORS → router dependency `get_current_user` (JWT, then the `Users` row) → `require_owner` → `order_service.checkout` → repositories → one commit that writes the order, copies prices, lowers stock, and marks the cart ordered → response model → HTTP 201.

If you can walk that list and say which constraint each step serves (trust, coordination, failure, change), you have the architecture. The pattern names are labels for those steps, not extra machinery.

---

## 11. How to keep learning without collecting labels

When a new name appears, ask four questions before adopting it.

1. Which constraint is it answering: time, space, failure, coordination, or change?
2. What boundary does it add, and what can no longer be a single local transaction or a single function call?
3. What did people do before it, and which of those costs came back?
4. Where is the primary source? A paper, an RFC, or the author's article beats a diagram with no date.

If the answer to the second question is "nothing important changes," the name is a synonym for a boundary you already have.

---

## References

Primary sources and the standard secondary accounts used above. RFCs are the internet's specifications. Books and papers are cited by the edition that introduced the idea.

1. D. L. Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules," *Communications of the ACM*, 15(12), 1972. https://doi.org/10.1145/361598.361623
2. J. von Neumann, "First Draft of a Report on the EDVAC," 1945. The stored-program description. A readable edition was later published in *IEEE Annals of the History of Computing*, 15(4), 1993.
3. D. M. Ritchie and K. Thompson, "The UNIX Time-Sharing System," *Communications of the ACM*, 17(7), 1974. https://doi.org/10.1145/361011.361061
4. Bell Labs and the Computer History Museum's Unix materials remain the narrative sources for 1969–1973. The CACM paper is the technical primary source.
5. E. W. Dijkstra, "The Structure of the 'THE'-Multiprogramming System," *Communications of the ACM*, 11(5), 1968. https://doi.org/10.1145/363095.363143
6. V. G. Cerf and R. E. Kahn, "A Protocol for Packet Network Intercommunication," *IEEE Transactions on Communications*, 22(5), 1974. The design paper behind TCP/IP.
7. J. Postel (ed.), "Internet Protocol," RFC 791, September 1981. https://www.rfc-editor.org/rfc/rfc791
8. T. Berners-Lee, "Information Management: A Proposal," CERN, 1989–1990, and the 1991 deployment of HTTP/HTML/URL. CERN's copy of the proposal is the primary document. https://www.w3.org/History/1989/proposal.html
9. R. T. Fielding, "Architectural Styles and the Design of Network-based Software Architectures," PhD dissertation, University of California, Irvine, 2000. Chapter 5 defines REST. https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm
10. E. Gamma, R. Helm, R. Johnson, J. Vlissides, *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
11. B. Meyer, *Object-Oriented Software Construction*. Prentice Hall, 1988. The open-closed principle.
12. B. Liskov, "Data Abstraction and Hierarchy," OOPSLA / *SIGPLAN Notices*, 1987.
13. B. Liskov and J. Wing, "A Behavioral Notion of Subtyping," *ACM Transactions on Programming Languages and Systems*, 16(6), 1994. https://doi.org/10.1145/197320.197383
14. R. C. Martin, "Design Principles and Design Patterns," 2000, and the book *Agile Software Development, Principles, Patterns, and Practices*, Prentice Hall, 2002. The principles later called SOLID, before the acronym.
15. The acronym SOLID is attributed to Michael Feathers, around 2004, in Martin's own later accounts and in the standard secondary summary. https://en.wikipedia.org/wiki/SOLID_(object-oriented_design) — use this only as the pointer to Feathers's role in the name, and prefer Martin's papers for the principles themselves. Martin's note "Getting a SOLID start" (2009) uses the acronym in public.
16. M. Fowler, *Patterns of Enterprise Application Architecture*. Addison-Wesley, 2002.
17. J. Lewis and M. Fowler, "Microservices," martinFowler.com, 25 March 2014. https://martinfowler.com/articles/microservices.html
18. M. E. Conway, "How Do Committees Invent?" *Datamation*, April 1968.
19. ISO/IEC 7498-1, "Information technology — Open Systems Interconnection — Basic Reference Model," first edition 1984. The seven-layer teaching model.
20. J. H. Saltzer, D. P. Reed, D. D. Clark, "End-to-End Arguments in System Design," *ACM Transactions on Computer Systems*, 2(4), 1984. https://doi.org/10.1145/357401.357402
21. R. Hinden and S. Deering, "IP Version 6 Addressing Architecture," RFC 4291, February 2006. `::1` is the loopback. https://www.rfc-editor.org/rfc/rfc4291
22. IANA, "IPv4 Special-Purpose Address Registry." `127.0.0.0/8`, name Loopback, allocation date 1981-09, reference RFC 1122 §3.2.1.3. https://www.iana.org/assignments/iana-ipv4-special-registry
23. M. Cotton, L. Vegoda, R. Bonica, B. Haberman, "Special-Purpose IP Address Registries," RFC 6890, April 2013. Table for `127.0.0.0/8`. https://www.rfc-editor.org/rfc/rfc6890
24. Y. Rekhter, B. Moskowitz, D. Karrenberg, G. J. de Groot, E. Lear, "Address Allocation for Private Internets," RFC 1918, February 1996. https://www.rfc-editor.org/rfc/rfc1918
25. IANA, "IPv4 Address Space." The `127/8` row, reserved, 1981-09. https://www.iana.org/assignments/ipv4-address-space
26. R. Braden (ed.), "Requirements for Internet Hosts — Communication Layers," RFC 1122, October 1989. Section 3.2.1.3, loopback. https://www.rfc-editor.org/rfc/rfc1122
27. S. Cheshire and M. Krochmal, "Special-Use Domain Names," RFC 6761, February 2013. The `localhost` name. https://www.rfc-editor.org/rfc/rfc6761
28. J. Postel (ed.), "Transmission Control Protocol," RFC 793, September 1981. 16-bit ports and the connection handshake. https://www.rfc-editor.org/rfc/rfc793
29. M. Cotton, L. Eggert, J. Touch, M. Westerlund, S. Cheshire, "Internet Assigned Numbers Authority (IANA) Procedures for the Management of the Service Name and Transport Protocol Port Number Registry," RFC 6335, August 2011. The three port ranges. https://www.rfc-editor.org/rfc/rfc6335
30. J. Touch, M. Kojo, E. Lear, A. Mankin, K. Ono, M. Stiemerling, L. Eggert, "Recommendations on Using Assigned Transport Port Numbers," RFC 7605, August 2015. https://www.rfc-editor.org/rfc/rfc7605
31. R. Fielding, M. Nottingham, J. Reschke (eds.), "HTTP Semantics," RFC 9110, and "HTTP/1.1," RFC 9112, June 2022. These obsolete RFC 2616 and are the current HTTP specification. Default port 80 is part of the `http` URI scheme, RFC 9110. https://www.rfc-editor.org/rfc/rfc9110
32. The fallacies of distributed computing are recorded by Bill Joy, Tom Lyon, Peter Deutsch, and James Gosling at Sun, and written up by Peter Deutsch and others from the mid-1990s. A stable secondary statement is on the Fallacies page that collects Deutsch's list. Arnon Rotem-Gal-Oz's commentary is a readable engineering expansion. Treat the list as engineering folklore with named authors, not as an RFC.
33. R. C. Martin, *Agile Software Development, Principles, Patterns, and Practices*. Prentice Hall, 2002.
34. R. C. Martin, *Clean Architecture*. Prentice Hall, 2017. The "one actor" wording of single responsibility, and the concentric circles.
35. A. Cockburn, "Hexagonal Architecture," 2005, with later revisions on alistair.cockburn.us. https://alistair.cockburn.us/hexagonal-architecture/
36. M. Nygard, *Release It!* Pragmatic Bookshelf, first edition 2007, second edition 2018. Timeouts, circuit breakers, bulkheads.
37. P. J. Eby, "Python Web Server Gateway Interface v1.0," PEP 333, 2003, and the Python 3 update PEP 3333. https://peps.python.org/pep-0333/
38. A. Godwin, "Inviting feedback on my proposed ASGI spec," Python Web-SIG, March 2016. https://mail.python.org/pipermail/web-sig/2016-March/005437.html
39. ASGI specification 3.0, 4 March 2019. The version history in the spec records 2.0 (2017-11-28) and 3.0 (2019-03-04). https://asgi.readthedocs.io/en/stable/specs/main.html
40. M. Jones, J. Bradley, N. Sakimura, "JSON Web Token (JWT)," RFC 7519, May 2015. https://www.rfc-editor.org/rfc/rfc7519
41. S. Ramírez, first public FastAPI source, commit `406c092`, 5 December 2018. `FastAPI` subclasses Starlette; Pydantic is already the schema layer. https://github.com/fastapi/fastapi/commit/406c092a3bf65bbd4405ce87611a7e0b9c0ae706
42. PyPI record for fastapi 0.1.0: Python `>=3.6`, dependencies `starlette>=0.9.7` and `pydantic>=0.16`. https://pypi.org/project/fastapi/0.1.0/
43. S. Ramírez, "Introducing FastAPI," the post collected in his blog-posts repository. The "shoulders of giants" statement (Starlette and Pydantic) and the account of trying not to write a framework. https://github.com/tiangolo/blog-posts/blob/master/introducing-fastapi/README.md and https://fastapi.tiangolo.com/
44. FastAPI release list, for versions after 0.1.0, including the 0.100 Pydantic v2 line and whatever is current when you read this. https://github.com/fastapi/fastapi/releases
45. E. Brewer, "Towards Robust Distributed Systems," PODC keynote, 2000. The CAP conjecture.
46. S. Gilbert and N. Lynch, "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services," *ACM SIGACT News*, 33(2), 2002. https://doi.org/10.1145/564585.564601
47. D. Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design," *IEEE Computer*, 45(2), 2012. PACELC.

A few books that hold the same material together if you want one spine after this guide: Parnas [1] for modules, Saltzer/Reed/Clark [20] for networks, Fielding [9] for the web, Fowler [16] [17] for application structure and services, Martin [34] for the circle drawing, Nygard [36] for production failure.
