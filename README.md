# Observatory

DIY Bitcoin observatory with basic block explorer capabilities meant to be easy to use and lightweight. 

## Requirements

* Linux only, tested on Ubuntu and Debian.
Should be fairly easy to make it work on Windows or Mac but I have no experience with neither of them.

* [Bitcoin Knots](https://bitcoinknots.org/).
This is required cause Knots offers `getblock` verbosity 3.
Knots will work right out of the box with your `.bitcoin` data folder, so you can effortlessly switch between Bitcoin Core and Bitcoin Knots.

* Python 3.7+ (should be already installed with most Linux distros).

## Setup

Clone or download the repository.

Open a terminal from the Observatory folder and run `sudo apt install python3-pip`, then pick one of the two below:

* ### Easy way

    * `python3 -m pip install -r advanced/requirements.txt`


* ### Hard way

    * `python3 -m pip install virtualenv`
    * `python3 -m virtualenv .env`
    * `source .env/bin/activate`
    * `pip3 install -r advanced/requirements.txt`

If you are in doubt between the two ways, you should try to use the virtualenv installation, this way you will keep you base system clean.
If you decide to go for it, remember that you'll have to run `source .env/bin/activate` as first command each time that you want to use the Observatory (check for `(.env)` at the beginning of the lines in your terminal).


Last thing is to set your RPC login credentials.
Open the `settings.py` file and edit `rpc_user` and `rpc_password` so that they match whatever you have in your `bitcoin.conf` file.

## Usage

Run [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/) from a terminal with `jupyter-lab`, if you are using virtualenv remember to first run `source .env/bin/activate` from the Observatory folder.

JupyterLab will open in your browser, ready to use.
If you are not familiar with Python and/or JupyterLab, you should start checking out the `Quickstart.ipynb`.

Enjoy!
