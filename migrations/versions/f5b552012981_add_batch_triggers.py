"""add batch triggers

Revision ID: f5b552012981
Revises: c24d0a3258d1
Create Date: 2017-09-01 10:44:40.093976

"""

# revision identifiers, used by Alembic.
revision = 'f5b552012981'
down_revision = 'c24d0a3258d1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

	# remove empty page
	op.execute("""
		create or replace function remove_empty_page()
		returns trigger as 
		$BODY$
		declare
			remaining integer;
		begin
			select count(1) into remaining from pagemembers where pageid = OLD.pageid;
		
			if(remaining = 0) then
				delete from pages where pageid = OLD.pageid;
			end if;

			return new;
		end
		$BODY$
		language 'plpgsql';

		drop trigger if exists remove_empty_page_trigger on pagemembers;
	
		create trigger remove_empty_page_trigger
		after delete on pagemembers
		for each row
		execute procedure remove_empty_page();
	""")

	# remove empty batch
	op.execute("""
		create or replace function remove_empty_batch()
		returns trigger as 
		$BODY$
		declare
			remaining integer;
		begin
			select count(1) into remaining from pages where batchid = OLD.batchid;
		
			if(remaining = 0) then
				delete from batches where batchid = OLD.batchid;
			end if;

			return new;
		end
		$BODY$
		language 'plpgsql';

		drop trigger if exists remove_empty_batch_trigger on pages;

		create trigger remove_empty_batch_trigger
		after delete on pages
		for each row
		execute procedure remove_empty_batch();
	""")


def downgrade():
	op.execute("drop trigger remove_empty_batch_trigger on pages");
	op.execute("drop function remove_empty_batch")
	
	op.execute("drop trigger remove_empty_page_trigger on pagemembers");
	op.execute("drop function remove_empty_page")
