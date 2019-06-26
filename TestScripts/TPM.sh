#!/bin/bash

# Test the TPM
#

# Initialization.

# Set up a hash of the passwd file. 
if [ ! -f hash.out ]; then
	tpm2_hash -H n -g 0x0004 -o hash.out /etc/passwd
	echo "TPM: hash.out created." 
fi

# Create a file to store random numbers.
if [ ! -f random.out ]; then
	touch random.out
	echo "TPM: random.out created."
fi

# Set up a non-voltile memory region.
if [ ! -f nvdata.out ]; then
	tpm2_getrandom 32 > nvdata.out
	EXITCODE=$?
	if [ "$EXITCODE" -ne 0 ]; then
		echo "ERROR: TPM: tpm2_getrandom call in initialization failed with $EXITCODE!"
	fi
	tpm2_nvdefine -x 0x1500001 -a 0x40000001 -s 160 -t 0x2000A
# Ignore the exit code from tpm2_nvdefine as the region may well already be defined from a previous run.
	tpm2_nvwrite -x 0x1500001 -a 0x40000001 nvdata.out
	EXITCODE=$?
	if [ "$EXITCODE" -ne 0 ]; then
		echo "ERROR: TPM: tpm2_nvwrite call in initialization failed with $EXITCODE!"
	fi
	echo "TPM: nvdata.out created, nv data region defined and filled."
fi

# Create some keys.
#if [ ! -f po.ctx ]; then
#	tpm2_createprimary -A e -g 0x000b -G rsa -C po.ctx
#	tpm2_createprimary -C po.ctx
#	tpm2_createprimary -o po.ctx
#	EXITCODE=$?
#	if [ "$EXITCODE" -ne 0 ]; then
#		echo "ERROR: TPM: tpm2_createprimary call in initialization failed with $EXITCODE!"
#	fi
#	tpm2_create -c po.ctx -g 0x000b -G 0x0001 -o key.pub -O key.priv
#	EXITCODE=$?
#	if [ "$EXITCODE" -ne 0 ]; then
#		echo "ERROR: TPM: tpm2_create call in initialization failed with $EXITCODE!"
#	fi
#	tpm2_load -c po.ctx -u key.pub -r key.priv -n key.name -C obj.ctx
#	EXITCODE=$?
#	if [ "$EXITCODE" -ne 0 ]; then
#		echo "ERROR: TPM: tpm2_load call in initialization failed with $EXITCODE!"
#	fi
#fi

# List the PCRs so we can see any changes.
# Lists sha1 and sha256 PCRs.
echo "TPM: PCR list."
tpm2_pcrlist
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_pcrlist call failed with $EXITCODE!"
	exit $EXITCODE
fi

# List the Non-Volatile (NV) memory regions.
echo "TPM: NV list."
tpm2_nvlist
EXITCODE=$?
if [ " $EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_nvlist call failed with $EXITCODE!"
	exit $EXITCODE
fi

# List the Persistent objects so we can see any changes.
echo "TPM: Persistent list."
tpm2_listpersistent
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_listpersistent call failed with $EXITCODE!"
	exit $EXITCODE
fi

# Exercise the RNG.
echo "TPM: New random number."
tpm2_getrandom 32 >>random.out
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_getrandom call failed with $EXITCODE!"
	exit $EXITCODE
fi

# Calculate a hash of the password file.
# Compare it to the previously calculated hash.
echo "TPM: Verify hash."
tpm2_hash -H n -g 0x0004 -o hash2.out /etc/passwd
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_hash call failed with $EXITCODE!"
	rm hash2.out
	exit $EXITCODE
fi
diff hash2.out hash.out
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: Hash values did not match!"
	rm hash2.out
	exit $EXITCODE
fi
rm hash2.out

# Check the nv memory.
# Compare it to the previously stored value.
echo "TPM: Verify NV memory."
tpm2_nvread -x 0x1500001 -a 0x40000001 -s 160 -o 0 -f nvdata2.out
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: tpm2_nvread call failed with $EXITCODE!"
	rm nvdata2.out
	exit $EXITCODE
fi
diff nvdata2.out nvdata.out
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	echo "ERROR: TPM: NV data value did not match original!"
	rm nvdata2.out
	exit $EXITCODE
fi
rm nvdata2.out

# Encrypt and Decrypt.
# Compare it to the previously stored value.
#echo "TPM: Encrypt"
#tpm2_rsaencrypt -c obj.ctx -o encrypted.out nvdata.out
#EXITCODE=$?
#if [ "$EXITCODE" -ne 0 ]; then
#	echo "ERROR: TPM: tpm2_rsaencrypt call failed with $EXITCODE!"
#	rm encrypted.out
#	exit $EXITCODE
#fi
#echo "TPM: Decrypt"
#tpm2_rsadecrypt -c obj.ctx -I encrypted.out -o nvdata2.out
#EXITCODE=$?
#if [ "$EXITCODE" -ne 0 ]; then
#	echo "ERROR: TPM: tpm2_rsadecrypt call failed with $EXITCODE!"
#	rm encrypted.out
#	rm nvdata2.out
#	exit $EXITCODE
#fi
#diff nvdata2.out nvdata.out
#EXITCODE=$?
#if [ "$EXITCODE" -ne 0 ]; then
#	echo "ERROR: TPM: Decrypted data values did not match original!"
#	rm encrypted.out
#	rm nvdata2.out
#	exit $EXITCODE
#fi
#rm encrypted.out
#rm nvdata2.out

# sign and Verify.
# Compare it to the previously stored value.
#echo "TPM: Sign"
#tpm2_sign -c obj.ctx -g 0x000b -m nvdata.out -s sig.out
#EXITCODE=$?
#if [ "$EXITCODE" -ne 0 ]; then
#	echo "ERROR: TPM: tpm2_sign call failed!"
#	rm sig.out
#	exit $EXITCODE
#fi
#echo "TPM: Verify"
#tpm2_verifysignature -c obj.ctx -g 0x000b -m nvdata.out -s sig.out -t tk.sig
#EXITCODE=$?
#if [ "$EXITCODE" -ne 0 ]; then
#	echo "ERROR: TPM: tpm2_verifysignature call failed!"
#	rm sig.out
#	rm tk.sig
#	exit $EXITCODE
#fi
#rm sig.out
#rm tk.sig

echo "TPM: Test completed."
# exit 0

