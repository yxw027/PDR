# StepDetection-and-StepLength-Estimation

Python Package / Application for pedestrian Dead Reckoning (PDR)



## Development

### Python3.x

1. Create a Virtual Environment

   ```bash
   $ virtualenv -m venv venv
   ```

2. Activate Virtual Environment

   ```bash
   $ . venv/bin/activate 
   ```

3. Install the Dependencies

   ```bash
   $ pip install -r requirements.txt
   ```

4. Install `pyrobomogen` as python package for development:

   ```bash
   $ pip install -e .
   ```

   This makes the `pdr` binary available as a CLI

### Usage

Run `pdr` binary using command line:

- -c configuration file path/name

```bash
$ pdr -c config.yaml
```



### Docker

1. To build Docker Images locally use:

   ```bash
   $ docker build -t pdr:<version> .
   ```

2. To run the Application with the `iotstack` network using:

   ```bash
   $ docker run --rm --network=iotstack -t pdr:<version> -c config.yaml
   ```

3. To run the a custom configuration for the Container use:

   ```bash
   $ docker run --rm -v $(pwd)/config.yaml:/pdr/config.yaml --network=iotstack -t pdr:<version> -c config.yaml
   ```

