#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';

import { NetworkStack } from '../lib/network-stack';
import { ComputeStack } from '../lib/compute-stack';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};

/**
 * Network Stack — VPC, public/private subnets, NAT
 */
const network = new NetworkStack(app, 'RestaurantNetworkStack', { env });

/**
 * Database Stack — RDS PostgreSQL + Secrets Manager credentials
 */
const database = new DatabaseStack(app, 'RestaurantDatabaseStack', {
  env,
  vpc: network.vpc,
});

/**
 * Cache Stack — ElastiCache Redis
 */
const cache = new CacheStack(app, 'RestaurantCacheStack', {
  env,
  vpc: network.vpc,
});

/**
 * Compute Stack — ECS cluster, Fargate services, ALB, ECR, autoscaling
 */
const compute = new ComputeStack(app, 'RestaurantComputeStack', {
  env,
  vpc: network.vpc,
  database: database.database,
  databaseSecret: database.database.secret,
  dbSecurityGroup: database.dbSecurityGroup,
  redisEndpoint: cache.redisEndpoint,
  redisSecurityGroup: cache.redisSecurityGroup,
  imageTag: app.node.tryGetContext('imageTag') ?? 'latest',
});

// Ensure data plane exists before compute wires secrets / endpoints
compute.addStackDependency(database);
compute.addStackDependency(cache);
compute.addStackDependency(network);

app.synth();
