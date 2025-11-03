# Using Cooja with Docker

## Step 1

If you already have a running Cooja container, you can skip this step.

If you don't have a Cooja container, you need to have Docker and Docker Compose installed on you computer.

In this directory, run: 
```bash
docker compose build
```
to build the required Docker image.

Right away, run:
```bash
docker compose up -d
```
to start the container `cooja_test` with SSH port 2230. See `docker-compose.yaml` for details.

## Step 2

In this step, we send the source code and configuration to Cooja container.

For example, if you are to send from the `examples/rpl-udp-tsch` directory, you should run following command from within the `cooja-tools` directory:

```bash
scp -P 2230 examples/rpl-udp-tsch/* root@127.0.0.1:/opt/contiki-ng/tools/cooja
```

The password for the `cooja_test` container is `root`.

Now, we send the Cooja configuration.

This configuration should be generated using the `json2cooja`tool.
```bash
scp -P 2230 json2cooja/output/* root@127.0.0.1:/opt/contiki-ng/tools/cooja
```

## Step 3

In this step, we connect to the container and run simulation.

Use the following command to establish an SSH connection:

```bash
ssh -p 2230 root@127.0.0.1
```

Once inside the container, go to the following directory:

```bash
cd /opt/contiki-ng/tools/cooja
```

Then, rename the XML configuration file:
```bash
mv simulation.xml simulation.csc
```

Running Cooja in non-iteractive mode:
```bash
java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
```

If everything is set up correctly, you will see the Cooja console log running.

Wait for this to finish before proceeding to the next step.


## Step 4

After the simulation finishes, to retrieve the log file, run following command from within the `cooja-tools` directory

```bash
scp -P 2230 root@127.0.0.1:/opt/contiki-ng/tools/cooja/COOJA.testlog log-analysis/input/cooja.log
```

Then, use the `analysis.py` script to generate statistics and graphs for the executed simulation.

---