#-------------------------------------------------------------------------------
# Name:        Convert DN to radiance 
# Purpose:
#
# Author:      Hoa
#
# Created:     20/07/2014
# Copyright:   (c) Hoa 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys, os, math, time 
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("spatial")

#Metadata exists in one of two standard formats (finds the correct name for each field)
def acquireMetadata(metadata, band):
    
    band = str(band)
    metadatalist = []
    
    if ("RADIANCE_MAXIMUM_BAND_" + band) in metadata.keys(): 
        BANDFILE = "FILE_NAME_BAND_" + band
        ML = "RADIANCE_MULT_BAND_" + band
        AL = "RADIANCE_ADD_BAND_" + band
        DATE = "DATE_ACQUIRED"
        metadatalist = [BANDFILE, ML, AL,DATE]

    else:
        arcpy.AddError('There was a problem reading the metadata for this file. Please make sure the _MTL.txt is in Level 1 data format')
        
    return metadatalist

#Calculate the radiance from metadata on band.
def calcRadiance (ML, AL, QCAL, band):
    
    ML = float(ML)
    AL = float(AL)
    inraster = Raster(QCAL)
    outname = 'Radiance_B'+str(band)+'.tif'

    arcpy.AddMessage('Band'+str(band))
    arcpy.AddMessage('ML ='+str(ML))
    arcpy.AddMessage('AL ='+str(AL))
    
    outraster = ML * inraster + AL
    outraster.save(outname)
    
    return outname


def readMetadata(metadataFile):

    f = metadataFile
    
    #Create an empty dictionary with which to populate all the metadata fields.
    metadata = {}

    #Each item in the txt document is seperated by a space and each key is
    #equated with '='. This loop strips and seperates then fills the dictonary.

    for line in f:
        if not line.strip() == "END":
            val = line.strip().split('=')
            metadata [val[0].strip()] = val[1].strip().strip('"')      
        else:
            break

    return metadata

#Takes the unicode parameter input from Arc and turns it into a nice python list
def cleanList(bandList):
    
    bandList = list(bandList)
    
    for x in range(len(bandList)):
        bandList[x] = str(bandList[x])
        
    while ';' in bandList:
        bandList.remove(';')
        
    return bandList

#////////////////////////////////////MAIN LOOP///////////////////////////////////////

#Parameters from Arc
env.workspace = arcpy.GetParameterAsText(0)
metadataPath = arcpy.GetParameterAsText(1)
keepRad = str(arcpy.GetParameterAsText(2))
bandList = cleanList(arcpy.GetParameterAsText(3))
arcpy.env.overwriteOutput = True

metadataFile = open(metadataPath)
metadata = readMetadata(metadataFile)
metadataFile.close()

successful = []
failed = []
for band in bandList:
    
    band = str(band)
    metlist = acquireMetadata(metadata, band)
    BANDFILE = metlist[0]
    ML = metlist[1]
    AL = metlist[2]
    DATE = metlist[3]

    try:
        radianceRaster = calcRadiance(metadata[ML], metadata[AL], metadata[BANDFILE], band)

        if keepRad != 'true':
            arcpy.Delete_management(radianceRaster)

        successful.append(BANDFILE)

    except Exception, e:
        failed.append(band)
        failed.append(str(e))

if successful:
    arcpy.AddWarning("The following files were converted successfully:")
    for x in successful:
        arcpy.AddWarning(metadata[x])

if failed:
    for x in range(0,len(failed),2):
        arcpy.AddError("Band" + str(failed[x]) + " failed to execute. Error: " + failed[x+1])
        if "object is not callable" in failed[x+1]:
            arcpy.AddError('This error catching is not 100%, it probably worked anyway')
