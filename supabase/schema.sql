-- CashPilot AI Database Schema for Supabase
-- Run this in Supabase SQL Editor to create all tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Users Table (extends Supabase auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- ============================================================================
-- Conversations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT conversations_title_length CHECK (char_length(title) <= 255)
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON public.conversations(updated_at DESC);

-- ============================================================================
-- Messages Table
-- ============================================================================
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE agent_type AS ENUM ('market', 'strategy', 'risk', 'general');

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    agent_type agent_type,
    metadata JSONB,
    CONSTRAINT messages_content_not_empty CHECK (char_length(content) > 0)
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON public.messages(timestamp DESC);

-- ============================================================================
-- Portfolios Table
-- ============================================================================
CREATE TYPE risk_tolerance AS ENUM ('conservative', 'moderate', 'aggressive');

CREATE TABLE IF NOT EXISTS public.portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    risk_tolerance risk_tolerance NOT NULL DEFAULT 'moderate',
    ada_balance DECIMAL(18, 6) NOT NULL DEFAULT 0,
    target_return DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT portfolios_name_length CHECK (char_length(name) <= 255),
    CONSTRAINT portfolios_ada_balance_positive CHECK (ada_balance >= 0),
    CONSTRAINT portfolios_target_return_range CHECK (target_return IS NULL OR (target_return >= 0 AND target_return <= 100))
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON public.portfolios(user_id);

-- ============================================================================
-- Positions Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES public.portfolios(id) ON DELETE CASCADE,
    protocol TEXT NOT NULL,
    pool TEXT,
    asset TEXT,
    amount_ada DECIMAL(18, 6) NOT NULL,
    allocation_percent DECIMAL(5, 2) NOT NULL,
    expected_apr DECIMAL(5, 2),
    risk_score INTEGER,
    entry_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT positions_protocol_length CHECK (char_length(protocol) <= 100),
    CONSTRAINT positions_amount_positive CHECK (amount_ada > 0),
    CONSTRAINT positions_allocation_range CHECK (allocation_percent >= 0 AND allocation_percent <= 100),
    CONSTRAINT positions_risk_score_range CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100))
);

CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON public.positions(portfolio_id);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

-- Conversations policies
CREATE POLICY "Users can view own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations"
    ON public.conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations"
    ON public.conversations FOR DELETE
    USING (auth.uid() = user_id);

-- Messages policies
CREATE POLICY "Users can view messages in own conversations"
    ON public.messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own conversations"
    ON public.messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.conversations
            WHERE conversations.id = messages.conversation_id
            AND conversations.user_id = auth.uid()
        )
    );

-- Portfolios policies
CREATE POLICY "Users can view own portfolios"
    ON public.portfolios FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own portfolios"
    ON public.portfolios FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own portfolios"
    ON public.portfolios FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own portfolios"
    ON public.portfolios FOR DELETE
    USING (auth.uid() = user_id);

-- Positions policies
CREATE POLICY "Users can view positions in own portfolios"
    ON public.positions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = positions.portfolio_id
            AND portfolios.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create positions in own portfolios"
    ON public.positions FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = positions.portfolio_id
            AND portfolios.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update positions in own portfolios"
    ON public.positions FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = positions.portfolio_id
            AND portfolios.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete positions in own portfolios"
    ON public.positions FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.portfolios
            WHERE portfolios.id = positions.portfolio_id
            AND portfolios.user_id = auth.uid()
        )
    );

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at
    BEFORE UPDATE ON public.portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON public.positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Initial Setup Complete!
-- ============================================================================

-- You can now:
-- 1. Enable Realtime for conversations and messages tables
-- 2. Configure Authentication providers
-- 3. Start using the API!
