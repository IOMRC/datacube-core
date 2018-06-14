from sqlalchemy import create_engine, SmallInteger, String, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.schema import Column, Table
from sqlalchemy.dialects import postgresql as postgres
from datacube.drivers.postgres._schema import DATASET_TYPE
from datacube.drivers.postgres._core import METADATA


EXTENT = Table('extent', METADATA,
               Column('id', postgres.UUID(as_uuid=True), primary_key=True),
               Column('dataset_type_ref', None, ForeignKey(DATASET_TYPE.c.id), nullable=False),
               Column('start', DateTime(timezone=True), nullable=False),
               Column('offset_alias', String, nullable=False),
               Column('geometry', postgres.JSONB, nullable=True)
              )

EXTENT_META = Table('extent_meta', METADATA,
                    Column('id', SmallInteger, primary_key=True, autoincrement=True),
                    Column('dataset_type_ref', None, ForeignKey(DATASET_TYPE.c.id), nullable=False),
                    Column('start', DateTime(timezone=True), nullable=False),
                    Column('end', DateTime(timezone=True), nullable=False),
                    Column('offset_alias', String, nullable=False),
                    Column('projection', String, nullable=True)
                   )

PRODUCT_BOUNDS = Table('product_bounds', METADATA,
                       Column('id', SmallInteger, primary_key=True, autoincrement=True),
                       Column('dataset_type_ref', None, ForeignKey(DATASET_TYPE.c.id), nullable=False),
                       Column('start', DateTime(timezone=True), nullable=False),
                       Column('end', DateTime(timezone=True), nullable=False),
                       Column('bounds', postgres.JSONB, nullable=True),
                       Column('projection', String, nullable=True)
                      )

if __name__ == '__main__':
    ENGINE = create_engine('postgresql://aj9439@agdcdev-db.nci.org.au:6432/datacube')
    # Create the extent table
    EXTENT.create(bind=ENGINE)
    # Create the extent_meta table
    EXTENT_META.create(bind=ENGINE)
    # Create product_bound table
    PRODUCT_BOUNDS.create(bind=ENGINE)
