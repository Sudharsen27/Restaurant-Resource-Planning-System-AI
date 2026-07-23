import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';

export interface CacheStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
}

export class CacheStack extends cdk.Stack {
  public readonly redisEndpoint: string;
  public readonly redisSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: CacheStackProps) {
    super(scope, id, props);

    this.redisSecurityGroup = new ec2.SecurityGroup(this, 'RedisSecurityGroup', {
      vpc: props.vpc,
      description: 'Security Group for Redis',
      allowAllOutbound: true,
    });

    const subnetGroup = new elasticache.CfnSubnetGroup(this, 'RedisSubnetGroup', {
      description: 'Subnet Group for Restaurant ERP Redis',
      subnetIds: props.vpc.privateSubnets.map(subnet => subnet.subnetId),
      cacheSubnetGroupName: 'restaurant-redis-subnet-group',
    });

    const redisCluster = new elasticache.CfnCacheCluster(this, 'RestaurantRedis', {
      engine: 'redis',
      cacheNodeType: 'cache.t3.micro',
      numCacheNodes: 1,
      clusterName: 'restaurant-redis',
      vpcSecurityGroupIds: [this.redisSecurityGroup.securityGroupId],
      cacheSubnetGroupName: subnetGroup.cacheSubnetGroupName!,
    });

    redisCluster.addDependency(subnetGroup);

    this.redisEndpoint = redisCluster.attrRedisEndpointAddress;

    new cdk.CfnOutput(this, 'RedisEndpoint', {
      value: this.redisEndpoint,
    });
  }
}