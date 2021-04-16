# pqrs

An user-facing tool for configuring local and remote machines using ansible
collections.

## Install

You can install `pqrs` simply using pip:

    pip install pqrs

## Usage

A typical workflow looks like follows:

    $ pqrs init  # intializes the PQRS configuration in ~/.pqrs/
    $ pqrs subscribe <url>  # subscribes to a given channel
    $ pqrs configure  # select the roles from the susbcribed channels
    $ pqrs update  # run to install roles / get updates
