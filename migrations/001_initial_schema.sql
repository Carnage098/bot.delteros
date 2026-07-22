CREATE TABLE IF NOT EXISTS guild_configs (
    guild_id BIGINT PRIMARY KEY,
    founder_id BIGINT NOT NULL,
    ceremony_channel_id BIGINT NOT NULL,
    log_channel_id BIGINT,
    admin_role_id BIGINT NOT NULL,
    staff_role_id BIGINT NOT NULL,
    moderator_role_id BIGINT NOT NULL,
    future_admin_role_id BIGINT NOT NULL,
    future_staff_role_id BIGINT NOT NULL,
    future_moderator_role_id BIGINT NOT NULL,
    quorum_percentage INTEGER NOT NULL DEFAULT 50 CHECK (quorum_percentage BETWEEN 1 AND 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nominations (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_configs(guild_id) ON DELETE CASCADE,
    candidate_id BIGINT NOT NULL,
    nominated_by_id BIGINT NOT NULL,
    rank TEXT NOT NULL CHECK (rank IN ('staff', 'moderator', 'administrator')),
    reason TEXT,
    status TEXT NOT NULL,
    current_commandment INTEGER NOT NULL DEFAULT 0,
    ceremony_channel_id BIGINT NOT NULL,
    ceremony_message_id BIGINT,
    vote_message_id BIGINT,
    pending_vote_kind TEXT,
    pending_founder_reason TEXT,
    decision_type TEXT,
    decision_by_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    probation_started_at TIMESTAMPTZ,
    promoted_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_nomination_per_candidate
ON nominations(guild_id, candidate_id)
WHERE status IN (
    'convocation', 'commandments', 'oath', 'suspended', 'nomination_vote',
    'waiting_founder', 'probation', 'final_confirmation', 'adoubement_vote'
);

CREATE TABLE IF NOT EXISTS commandment_acceptances (
    nomination_id BIGINT NOT NULL REFERENCES nominations(id) ON DELETE CASCADE,
    commandment_number INTEGER NOT NULL CHECK (commandment_number BETWEEN 1 AND 12),
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (nomination_id, commandment_number)
);

CREATE TABLE IF NOT EXISTS council_votes (
    nomination_id BIGINT NOT NULL REFERENCES nominations(id) ON DELETE CASCADE,
    vote_kind TEXT NOT NULL CHECK (vote_kind IN ('nomination', 'adoubement')),
    voter_id BIGINT NOT NULL,
    choice TEXT NOT NULL CHECK (choice IN ('approve', 'reject', 'abstain')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (nomination_id, vote_kind, voter_id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id BIGSERIAL PRIMARY KEY,
    nomination_id BIGINT NOT NULL REFERENCES nominations(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('positive', 'neutral', 'negative')),
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ceremony_logs (
    id BIGSERIAL PRIMARY KEY,
    nomination_id BIGINT REFERENCES nominations(id) ON DELETE SET NULL,
    guild_id BIGINT NOT NULL,
    actor_id BIGINT,
    event_type TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nominations_guild_status ON nominations(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_logs_nomination ON ceremony_logs(nomination_id, created_at);
