"""Initial migration

Revision ID: 7da3813021ac
Revises: 
Create Date: 2024-11-19 12:08:01.303210+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7da3813021ac'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scraping_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('last_run', sa.DateTime(), nullable=True),
    sa.Column('next_run', sa.DateTime(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('success_count', sa.Integer(), nullable=True),
    sa.Column('fail_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraping_tasks_status'), 'scraping_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_scraping_tasks_url'), 'scraping_tasks', ['url'], unique=False)
    op.create_table('scholarships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('amount', sa.String(length=100), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=True),
    sa.Column('field_of_study', sa.String(length=200), nullable=True),
    sa.Column('level_of_study', sa.String(length=100), nullable=True),
    sa.Column('eligibility_criteria', sa.Text(), nullable=True),
    sa.Column('application_url', sa.String(length=500), nullable=True),
    sa.Column('source_url', sa.String(length=500), nullable=True),
    sa.Column('location_of_study', sa.String(length=200), nullable=True),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('amount_normalized_min', sa.Float(), nullable=True),
    sa.Column('amount_normalized_max', sa.Float(), nullable=True),
    sa.Column('amount_type', sa.String(length=50), nullable=True),
    sa.Column('is_renewable', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['scraping_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scholarships_confidence_score'), 'scholarships', ['confidence_score'], unique=False)
    op.create_index(op.f('ix_scholarships_deadline'), 'scholarships', ['deadline'], unique=False)
    op.create_index(op.f('ix_scholarships_field_of_study'), 'scholarships', ['field_of_study'], unique=False)
    op.create_index(op.f('ix_scholarships_level_of_study'), 'scholarships', ['level_of_study'], unique=False)
    op.create_index(op.f('ix_scholarships_source_url'), 'scholarships', ['source_url'], unique=False)
    op.create_index(op.f('ix_scholarships_task_id'), 'scholarships', ['task_id'], unique=False)
    op.create_index(op.f('ix_scholarships_title'), 'scholarships', ['title'], unique=False)
    op.create_table('scraped_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=500), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('classification', sa.String(length=50), nullable=True),
    sa.Column('found_at', sa.DateTime(), nullable=True),
    sa.Column('processed', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['scraping_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraped_links_classification'), 'scraped_links', ['classification'], unique=False)
    op.create_index(op.f('ix_scraped_links_processed'), 'scraped_links', ['processed'], unique=False)
    op.create_index(op.f('ix_scraped_links_task_id'), 'scraped_links', ['task_id'], unique=False)
    op.create_index(op.f('ix_scraped_links_url'), 'scraped_links', ['url'], unique=False)
    op.create_table('scraping_progress',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('total_links', sa.Integer(), nullable=True),
    sa.Column('processed_links', sa.Integer(), nullable=True),
    sa.Column('scholarships_found', sa.Integer(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('processing_duration', sa.Float(), nullable=True),
    sa.Column('last_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['scraping_tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraping_progress_id'), 'scraping_progress', ['id'], unique=False)
    op.create_index(op.f('ix_scraping_progress_status'), 'scraping_progress', ['status'], unique=False)
    op.create_index(op.f('ix_scraping_progress_task_id'), 'scraping_progress', ['task_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_scraping_progress_task_id'), table_name='scraping_progress')
    op.drop_index(op.f('ix_scraping_progress_status'), table_name='scraping_progress')
    op.drop_index(op.f('ix_scraping_progress_id'), table_name='scraping_progress')
    op.drop_table('scraping_progress')
    op.drop_index(op.f('ix_scraped_links_url'), table_name='scraped_links')
    op.drop_index(op.f('ix_scraped_links_task_id'), table_name='scraped_links')
    op.drop_index(op.f('ix_scraped_links_processed'), table_name='scraped_links')
    op.drop_index(op.f('ix_scraped_links_classification'), table_name='scraped_links')
    op.drop_table('scraped_links')
    op.drop_index(op.f('ix_scholarships_title'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_task_id'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_source_url'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_level_of_study'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_field_of_study'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_deadline'), table_name='scholarships')
    op.drop_index(op.f('ix_scholarships_confidence_score'), table_name='scholarships')
    op.drop_table('scholarships')
    op.drop_index(op.f('ix_scraping_tasks_url'), table_name='scraping_tasks')
    op.drop_index(op.f('ix_scraping_tasks_status'), table_name='scraping_tasks')
    op.drop_table('scraping_tasks')
    # ### end Alembic commands ###
