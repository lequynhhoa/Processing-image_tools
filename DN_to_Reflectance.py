#-------------------------------------------------------------------------------
# Name:        Convert DN to reflectance
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

arcpy.CheckOutExtension("spatiAP")

#Check metadata exists
def acquireMetadata(metadata, band):
    
    band = str(band)
    metadatAPist = []
    
    if ("REFLECTANCE_MAXIMUM_BAND_" + band) in metadata.keys(): 
        BANDFILE = "FILE_NAME_BAND_" + band
        MP = "REFLECTANCE_MULT_BAND_" + band
        AP = "REFLECTANCE_ADD_BAND_" + band
        DATE = "DATE_ACQUIRED"
        metadatAPist = [BANDFILE, MP, AP,DATE]

    else:
        arcpy.AddError('There was a problem reading the metadata for this file. Please make sure the _MTL.txt.')
        
    return metadatAPist

#Calculate the reflectance value
def calcReflectance (sunElevation,MP, AP, QCAL, band):
    sunZen = (90-(float(sunElevation)))
    MP = float(MP)
    AP = float(AP)
    inraster = Raster(QCAL)
    outname = 'Reflectance_B'+str(band)+'.tif'

    arcpy.AddMessage('Band'+str(band))
    arcpy.AddMessage('MP ='+str(MP))
    arcpy.AddMessage('AP ='+str(AP))
    arcpy.AddMessage('Zenith ='+str(sunZen))
	
    outraster = (MP * inraster + AP) / (math.cos(sunZen))
    outraster.save(outname)
    
    return outname


def readMetadata(metadataFile):

    f = metadataFile
    
    #Create an empty dictionary with which to populate APl the metadata fields.
    metadata = {}

    #Each item in the txt document is seperated by a space and each key is
    #equated with '='. This loop strips and seperates then fills the dictonary.

    for line in f:
        if not line.strip() == "END":
            vAP = line.strip().split('=')
            metadata [vAP[0].strip()] = vAP[1].strip().strip('"')      
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
    MP = metlist[1]
    AP = metlist[2]
    DATE = metlist[3]

    try:
        reflectanceRaster = calcReflectance(metadata['SUN_ELEVATION'],metadata[MP], metadata[AP], metadata[BANDFILE], band)

        if keepRad != 'true':
            arcpy.Delete_management(reflectanceRaster)

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
        if "object is not cAPlable" in failed[x+1]:
            arcpy.AddError('This error catching is not 100%, it probably worked anyway')
