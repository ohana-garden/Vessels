/**
 * Vessels Payment Service Entry Point
 *
 * GraphQL API for payment operations integrated with TigerBeetle ledger.
 * Runs inside the main Vessels container as a subprocess.
 */

import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { OhanaLedger } from './services/ohana-ledger.js';
import { MojaloopConnector } from './services/mojaloop-connector.js';
import { Pool } from 'pg';
import { readFileSync } from 'fs';

// ============================================================================
// Configuration
// ============================================================================

const PORT = parseInt(process.env.PORT || '3000');
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://vessels:password@localhost:5432/vessels_payment';
const TIGERBEETLE_REPLICAS = (process.env.TIGERBEETLE_REPLICA_ADDRESSES || 'localhost:3001').split(',');

// ============================================================================
// Initialize Services
// ============================================================================

const db = new Pool({
  connectionString: DATABASE_URL,
  max: 10,
});

const ledger = new OhanaLedger({
  tigerbeetleClusterIds: [0],
  tigerbeetleReplicas: TIGERBEETLE_REPLICAS,
});

let mojaloop: MojaloopConnector | null = null;

if (process.env.MOJALOOP_ENABLED === 'true') {
  mojaloop = new MojaloopConnector({
    mojaloop: {
      switchUrl: process.env.MOJALOOP_SWITCH_URL!,
      participantId: process.env.MOJALOOP_PARTICIPANT_ID!,
      apiKey: process.env.MOJALOOP_API_KEY!,
      callbackUrl: process.env.MOJALOOP_CALLBACK_URL!,
    },
    ledger,
    database: db,
    fallbackToACH: true,
  });
}

// ============================================================================
// GraphQL Schema
// ============================================================================

const typeDefs = `#graphql
  type Query {
    health: HealthStatus!
    accountBalance(vendorId: String!, accountType: String!): Balance!
    transactionHistory(vendorId: String!, limit: Int): [Transaction!]!
  }

  type Mutation {
    createVendor(vendorId: String!, name: String!): Vendor!
    transfer(
      fromVendorId: String!
      toVendorId: String!
      amountUsd: Float!
      description: String
    ): TransferResult!

    payout(
      vendorId: String!
      amountUsd: Float!
      method: PayoutMethod!
    ): PayoutResult!
  }

  type HealthStatus {
    status: String!
    tigerbeetle: Boolean!
    mojaloop: Boolean
    database: Boolean!
  }

  type Balance {
    vendorId: String!
    accountType: String!
    balanceUsd: Float!
    asOf: String!
  }

  type Transaction {
    id: String!
    fromVendor: String!
    toVendor: String!
    amountUsd: Float!
    description: String
    timestamp: String!
  }

  type Vendor {
    id: String!
    name: String!
    createdAt: String!
  }

  type TransferResult {
    transferId: String!
    status: String!
    amountUsd: Float!
  }

  type PayoutResult {
    payoutId: String!
    status: String!
    amountUsd: Float!
    feesUsd: Float!
  }

  enum PayoutMethod {
    ACH
    RTP
    MOJALOOP
    CARD
  }
`;

// ============================================================================
// Resolvers
// ============================================================================

const resolvers = {
  Query: {
    health: async () => {
      const dbHealthy = await db.query('SELECT 1')
        .then(() => true)
        .catch(() => false);

      const mojaloopHealth = mojaloop
        ? await mojaloop.healthCheck()
        : { mojaloop: false, database: false };

      return {
        status: 'ok',
        tigerbeetle: true, // TODO: Add actual health check
        mojaloop: mojaloopHealth.mojaloop || false,
        database: dbHealthy,
      };
    },

    accountBalance: async (_: any, { vendorId, accountType }: any) => {
      const balance = await ledger.getBalance(vendorId, accountType);
      return {
        vendorId,
        accountType,
        balanceUsd: balance,
        asOf: new Date().toISOString(),
      };
    },

    transactionHistory: async (_: any, { vendorId, limit = 50 }: any) => {
      const result = await db.query(
        `SELECT * FROM transactions WHERE vendor_id = $1 ORDER BY created_at DESC LIMIT $2`,
        [vendorId, limit]
      );

      return result.rows.map(row => ({
        id: row.id,
        fromVendor: row.from_vendor,
        toVendor: row.to_vendor,
        amountUsd: parseFloat(row.amount_usd),
        description: row.description,
        timestamp: row.created_at.toISOString(),
      }));
    },
  },

  Mutation: {
    createVendor: async (_: any, { vendorId, name }: any) => {
      await ledger.createVendorAccounts(vendorId, name);

      await db.query(
        `INSERT INTO vendors (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING`,
        [vendorId, name]
      );

      return {
        id: vendorId,
        name,
        createdAt: new Date().toISOString(),
      };
    },

    transfer: async (_: any, args: any) => {
      const result = await ledger.transfer({
        fromEntityId: args.fromVendorId,
        fromAccountType: 'vendor_get_reserve',
        toEntityId: args.toVendorId,
        toAccountType: 'vendor_get_reserve',
        amountUsd: args.amountUsd,
        description: args.description,
      });

      return {
        transferId: result.transferId,
        status: 'completed',
        amountUsd: args.amountUsd,
      };
    },

    payout: async (_: any, { vendorId, amountUsd, method }: any) => {
      if (method === 'MOJALOOP' && mojaloop) {
        // Mojaloop payout - requires destination DFSP
        // For now, return placeholder
        return {
          payoutId: 'mojaloop-placeholder',
          status: 'pending',
          amountUsd,
          feesUsd: 0,
        };
      }

      // Other payout methods - placeholder
      return {
        payoutId: `${method.toLowerCase()}-${Date.now()}`,
        status: 'pending',
        amountUsd,
        feesUsd: method === 'ACH' ? 0 : 0.50,
      };
    },
  },
};

// ============================================================================
// Start Server
// ============================================================================

const server = new ApolloServer({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  listen: { port: PORT },
  context: async ({ req }) => ({
    db,
    ledger,
    mojaloop,
  }),
});

console.log(`🚀 Vessels Payment Service ready at ${url}`);
console.log(`   - TigerBeetle: ${TIGERBEETLE_REPLICAS.join(', ')}`);
console.log(`   - Mojaloop: ${mojaloop ? 'enabled' : 'disabled'}`);
console.log(`   - Database: ${DATABASE_URL.replace(/:[^:@]+@/, ':***@')}`);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing connections...');
  await ledger.close();
  await db.end();
  process.exit(0);
});
