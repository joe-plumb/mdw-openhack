# Databricks notebook source
# MAGIC %md
# MAGIC # Config

# COMMAND ----------

container_name = "mdwoh"
blobaccountname = "mdwohwe01"

if not any(mount.mountPoint == f"/mnt/{container_name}" for mount in dbutils.fs.mounts()):
  dbutils.fs.mount(
    source = f"wasbs://{container_name}@{blobaccountname}.blob.core.windows.net", 
    mount_point = f"/mnt/{container_name}",
    extra_configs = {f"fs.azure.account.key.{blobaccountname}.blob.core.windows.net":dbutils.secrets.get(scope = "mdwoh01", key = "mdwohwe01")})

# COMMAND ----------

from pyspark.sql.functions import col, lit, concat

# COMMAND ----------

# CustomerID	String	
# LastName	String	
# FirstName	String	
# PhoneNumber	String	
# CreatedDate	DateTime	DateTime
# UpdatedDate	DateTime	DateTime
# SourceID	Integer	1 = Southridge, 2 = VanArsdel Ltd, 3 = Fourth Coffee
# UniqueID	String	CONCAT SourceID + CustomerID

from pyspark.sql.types import *

sr_schema = StructType([
    StructField("CustomerID",StringType(),True)
  , StructField("LastName",StringType(),True)
  , StructField("FirstName",StringType(),True)
  , StructField("PhoneNumber",StringType(),True)
  , StructField("CreatedDate",TimestampType(),True)
  , StructField("UpdatedDate",TimestampType(),True)])

va_schema = StructType([
    StructField("CustomerID",StringType(),True)
  , StructField("LastName",StringType(),True)
  , StructField("FirstName",StringType(),True)
  , StructField("AddressLine1",StringType(),True)
  , StructField("AddressLine2",StringType(),True)
  , StructField("City",TimestampType(),True)
  , StructField("State",StringType(),True)
  , StructField("ZipCode",StringType(),True)
  , StructField("PhoneNumber",StringType(),True)
  , StructField("CreatedDate",TimestampType(),True)
  , StructField("UpdatedDate",TimestampType(),True)])

# COMMAND ----------

# load data into df with source IDs
sr_df = spark.read.format('csv').options(header='true').schema(sr_schema).load("/mnt/mdwoh/raw/CloudSales/dbo/dbo.Customers").withColumn("SourceID", lit(1))
va_df = spark.read.format('csv').options(header='true').schema(va_schema).load("/mnt/mdwoh/raw/VanArsdel/OnPremRentals/dbo/dbo.Customers").withColumn("SourceID", lit(2))

# select columns
sr_df = sr_df.select("SourceID", "CustomerID", "LastName", "FirstName", "PhoneNumber", "CreatedDate", "UpdatedDate").withColumn("UniqueID", concat(col("SourceID"), col("CustomerID")))
va_df = va_df.select("SourceID", "CustomerID", "LastName", "FirstName", "PhoneNumber", "CreatedDate", "UpdatedDate").withColumn("UniqueID", concat(col("SourceID"), col("CustomerID")))

# merge data frames
df = sr_df.union(va_df)  

# display(df)
# write to storage 
df.write.format("delta").mode("overwrite").save("/mnt/mdwoh/curated/Customers/")
