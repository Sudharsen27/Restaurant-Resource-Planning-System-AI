import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as rds from 'aws-cdk-lib/aws-rds';

export interface ComputeStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
  /** RDS instance from DatabaseStack (for endpoint). */
  database?: rds.IDatabaseInstance;
  /** RDS credentials secret (Secrets Manager). */
  databaseSecret?: secretsmanager.ISecret;
  /** RDS security group — ingress from ECS is added here (cross-stack). */
  dbSecurityGroup?: ec2.ISecurityGroup;
  /** ElastiCache primary endpoint hostname. */
  redisEndpoint?: string;
  /**
   * Optional Redis SG. Pass when available so ECS can reach Redis on 6379.
   */
  redisSecurityGroup?: ec2.ISecurityGroup;
  /** Container image tag (default: latest). */
  imageTag?: string;
}

/**
 * ECS Fargate compute for Restaurant ERP:
 * ALB + backend / frontend / worker services, ECR repos, Secrets Manager, autoscaling.
 */
export class ComputeStack extends cdk.Stack {
  public readonly cluster: ecs.Cluster;
  public readonly loadBalancer: elbv2.ApplicationLoadBalancer;
  public readonly backendService: ecs.FargateService;
  public readonly frontendService: ecs.FargateService;
  public readonly workerService: ecs.FargateService;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const imageTag = props.imageTag ?? 'latest';
    const dbName = 'restaurant_rps';
    const dbUser = 'postgres';

    // -------------------------------------------------------------------------
    // Logging
    // -------------------------------------------------------------------------
    const logGroup = new logs.LogGroup(this, 'RestaurantLogGroup', {
      logGroupName: '/restaurant-erp/ecs',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // -------------------------------------------------------------------------
    // Cluster
    // -------------------------------------------------------------------------
    this.cluster = new ecs.Cluster(this, 'RestaurantCluster', {
      clusterName: 'restaurant-erp-cluster',
      vpc: props.vpc,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

    // -------------------------------------------------------------------------
    // ECR repositories (pre-existing — import, do not create)
    // -------------------------------------------------------------------------
    const backendRepo = ecr.Repository.fromRepositoryName(
      this,
      'BackendRepository',
      'restaurant-erp-backend',
    );

    const frontendRepo = ecr.Repository.fromRepositoryName(
      this,
      'FrontendRepository',
      'restaurant-erp-frontend',
    );

    const workerRepo = ecr.Repository.fromRepositoryName(
      this,
      'WorkerRepository',
      'restaurant-erp-worker',
    );

    // -------------------------------------------------------------------------
    // Application secret (SECRET_KEY + non-DB secrets)
    // -------------------------------------------------------------------------
    const appSecret = new secretsmanager.Secret(this, 'AppSecret', {
      secretName: 'restaurant-erp/app',
      description: 'RRPS application secrets (SECRET_KEY, etc.)',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          APP_ENV: 'production',
        }),
        generateStringKey: 'SECRET_KEY',
        excludePunctuation: true,
        passwordLength: 48,
      },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // -------------------------------------------------------------------------
    // Security groups
    // -------------------------------------------------------------------------
    const albSg = new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
      vpc: props.vpc,
      description: 'ALB — public HTTP',
      allowAllOutbound: true,
    });
    albSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'HTTP from Internet');

    const backendSg = new ec2.SecurityGroup(this, 'BackendSecurityGroup', {
      vpc: props.vpc,
      description: 'ECS backend tasks',
      allowAllOutbound: true,
    });
    backendSg.addIngressRule(albSg, ec2.Port.tcp(8000), 'API from ALB');

    const frontendSg = new ec2.SecurityGroup(this, 'FrontendSecurityGroup', {
      vpc: props.vpc,
      description: 'ECS frontend tasks',
      allowAllOutbound: true,
    });
    frontendSg.addIngressRule(albSg, ec2.Port.tcp(80), 'HTTP from ALB');

    const workerSg = new ec2.SecurityGroup(this, 'WorkerSecurityGroup', {
      vpc: props.vpc,
      description: 'ECS Celery worker tasks',
      allowAllOutbound: true,
    });

    if (props.dbSecurityGroup) {
      // Ingress resources live in THIS stack to avoid Database↔Compute cycles.
      new ec2.CfnSecurityGroupIngress(this, 'PostgresFromBackend', {
        groupId: props.dbSecurityGroup.securityGroupId,
        sourceSecurityGroupId: backendSg.securityGroupId,
        ipProtocol: 'tcp',
        fromPort: 5432,
        toPort: 5432,
        description: 'Postgres from backend ECS',
      });
      new ec2.CfnSecurityGroupIngress(this, 'PostgresFromWorker', {
        groupId: props.dbSecurityGroup.securityGroupId,
        sourceSecurityGroupId: workerSg.securityGroupId,
        ipProtocol: 'tcp',
        fromPort: 5432,
        toPort: 5432,
        description: 'Postgres from worker ECS',
      });
    }

    if (props.redisSecurityGroup) {
      new ec2.CfnSecurityGroupIngress(this, 'RedisFromBackend', {
        groupId: props.redisSecurityGroup.securityGroupId,
        sourceSecurityGroupId: backendSg.securityGroupId,
        ipProtocol: 'tcp',
        fromPort: 6379,
        toPort: 6379,
        description: 'Redis from backend ECS',
      });
      new ec2.CfnSecurityGroupIngress(this, 'RedisFromWorker', {
        groupId: props.redisSecurityGroup.securityGroupId,
        sourceSecurityGroupId: workerSg.securityGroupId,
        ipProtocol: 'tcp',
        fromPort: 6379,
        toPort: 6379,
        description: 'Redis from worker ECS',
      });
    }

    // -------------------------------------------------------------------------
    // IAM — task execution + task roles
    // -------------------------------------------------------------------------
    const executionRole = new iam.Role(this, 'EcsTaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AmazonECSTaskExecutionRolePolicy',
        ),
      ],
    });
    appSecret.grantRead(executionRole);
    props.databaseSecret?.grantRead(executionRole);
    backendRepo.grantPull(executionRole);
    frontendRepo.grantPull(executionRole);
    workerRepo.grantPull(executionRole);

    const taskRole = new iam.Role(this, 'EcsTaskRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'Application role for RRPS containers (S3, Secrets, etc.)',
    });
    appSecret.grantRead(taskRole);
    props.databaseSecret?.grantRead(taskRole);

    // -------------------------------------------------------------------------
    // Shared env / secrets for backend + worker
    // -------------------------------------------------------------------------
    const redisHost = props.redisEndpoint ?? 'localhost';

    const commonEnvironment: Record<string, string> = {
      APP_ENV: 'production',
      DEBUG: 'false',
      LOG_FORMAT: 'json',
      LOG_LEVEL: 'INFO',
      REDIS_ENABLED: 'true',
      REDIS_URL: `redis://${redisHost}:6379/0`,
      CELERY_BROKER_URL: `redis://${redisHost}:6379/1`,
      CELERY_RESULT_BACKEND: `redis://${redisHost}:6379/2`,
      CELERY_TASK_ALWAYS_EAGER: 'false',
      STORAGE_BACKEND: 'local',
      SEED_ENTERPRISE_DATA: 'false',
      SEED_LEGACY_FORECASTS: 'false',
      RATE_LIMIT_ENABLED: 'true',
      METRICS_ENABLED: 'true',
      CORS_ORIGINS: '*', // tighten after HTTPS/custom domain
    };

    if (props.database && props.databaseSecret) {
      // CloudFormation dynamic reference keeps the password out of plaintext CFN params.
      const secretArn = props.databaseSecret.secretArn;
      commonEnvironment.DATABASE_URL =
        `postgresql://${dbUser}:{{resolve:secretsmanager:${secretArn}:SecretString:password}}` +
        `@${props.database.dbInstanceEndpointAddress}:5432/${dbName}`;
    }

    const commonSecrets: Record<string, ecs.Secret> = {
      SECRET_KEY: ecs.Secret.fromSecretsManager(appSecret, 'SECRET_KEY'),
    };

    const logDriver = (streamPrefix: string) =>
      ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix,
      });

    // -------------------------------------------------------------------------
    // Backend task definition + service
    // -------------------------------------------------------------------------
    const backendTd = new ecs.FargateTaskDefinition(this, 'BackendTaskDef', {
      family: 'restaurant-erp-backend',
      cpu: 512,
      memoryLimitMiB: 1024,
      executionRole,
      taskRole,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    backendTd.addContainer('backend', {
      image: ecs.ContainerImage.fromEcrRepository(backendRepo, imageTag),
      logging: logDriver('backend'),
      environment: commonEnvironment,
      secrets: commonSecrets,
      portMappings: [{ containerPort: 8000, protocol: ecs.Protocol.TCP }],
      healthCheck: {
        command: [
          'CMD-SHELL',
          'curl -fsS http://127.0.0.1:8000/health/live || exit 1',
        ],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(60),
      },
    });

    this.backendService = new ecs.FargateService(this, 'BackendService', {
      serviceName: 'restaurant-erp-backend',
      cluster: this.cluster,
      taskDefinition: backendTd,
      desiredCount: 2,
      assignPublicIp: false,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [backendSg],
      circuitBreaker: { rollback: true },
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
      enableExecuteCommand: true,
    });

    // -------------------------------------------------------------------------
    // Frontend task definition + service
    // -------------------------------------------------------------------------
    const frontendTd = new ecs.FargateTaskDefinition(this, 'FrontendTaskDef', {
      family: 'restaurant-erp-frontend',
      cpu: 256,
      memoryLimitMiB: 512,
      executionRole,
      taskRole,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    frontendTd.addContainer('frontend', {
      image: ecs.ContainerImage.fromEcrRepository(frontendRepo, imageTag),
      logging: logDriver('frontend'),
      environment: {
        // Build-time VITE_* is baked into the image; runtime nginx serves static files.
        NGINX_HOST: '0.0.0.0',
      },
      portMappings: [{ containerPort: 80, protocol: ecs.Protocol.TCP }],
      healthCheck: {
        command: ['CMD-SHELL', 'wget -qO- http://127.0.0.1/ || exit 1'],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
        startPeriod: cdk.Duration.seconds(20),
      },
    });

    this.frontendService = new ecs.FargateService(this, 'FrontendService', {
      serviceName: 'restaurant-erp-frontend',
      cluster: this.cluster,
      taskDefinition: frontendTd,
      desiredCount: 2,
      assignPublicIp: false,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [frontendSg],
      circuitBreaker: { rollback: true },
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
    });

    // -------------------------------------------------------------------------
    // Worker task definition + service (Celery)
    // -------------------------------------------------------------------------
    const workerTd = new ecs.FargateTaskDefinition(this, 'WorkerTaskDef', {
      family: 'restaurant-erp-worker',
      cpu: 512,
      memoryLimitMiB: 1024,
      executionRole,
      taskRole,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    workerTd.addContainer('worker', {
      image: ecs.ContainerImage.fromEcrRepository(workerRepo, imageTag),
      logging: logDriver('worker'),
      environment: commonEnvironment,
      secrets: commonSecrets,
      // Dockerfile.worker default CMD is celery worker
    });

    this.workerService = new ecs.FargateService(this, 'WorkerService', {
      serviceName: 'restaurant-erp-worker',
      cluster: this.cluster,
      taskDefinition: workerTd,
      desiredCount: 1,
      assignPublicIp: false,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [workerSg],
      circuitBreaker: { rollback: true },
      enableExecuteCommand: true,
    });

    // -------------------------------------------------------------------------
    // Application Load Balancer + target groups + listener
    // -------------------------------------------------------------------------
    this.loadBalancer = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      loadBalancerName: 'restaurant-erp-alb',
      vpc: props.vpc,
      internetFacing: true,
      securityGroup: albSg,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      deletionProtection: false,
    });

    const backendTg = new elbv2.ApplicationTargetGroup(this, 'BackendTargetGroup', {
      targetGroupName: 'restaurant-erp-backend',
      vpc: props.vpc,
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        enabled: true,
        path: '/health/live',
        healthyHttpCodes: '200',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
      },
      deregistrationDelay: cdk.Duration.seconds(30),
    });
    this.backendService.attachToApplicationTargetGroup(backendTg);

    const frontendTg = new elbv2.ApplicationTargetGroup(this, 'FrontendTargetGroup', {
      targetGroupName: 'restaurant-erp-frontend',
      vpc: props.vpc,
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        enabled: true,
        path: '/',
        healthyHttpCodes: '200-399',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
      },
      deregistrationDelay: cdk.Duration.seconds(30),
    });
    this.frontendService.attachToApplicationTargetGroup(frontendTg);

    const listener = this.loadBalancer.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultAction: elbv2.ListenerAction.forward([frontendTg]),
    });

    listener.addTargetGroups('ApiRoutes', {
      priority: 10,
      conditions: [elbv2.ListenerCondition.pathPatterns(['/api/*'])],
      targetGroups: [backendTg],
    });

    listener.addTargetGroups('HealthRoutes', {
      priority: 20,
      conditions: [elbv2.ListenerCondition.pathPatterns(['/health', '/health/*'])],
      targetGroups: [backendTg],
    });

    listener.addTargetGroups('DocsRoutes', {
      priority: 30,
      conditions: [
        elbv2.ListenerCondition.pathPatterns([
          '/docs',
          '/docs/*',
          '/redoc',
          '/redoc/*',
          '/openapi.json',
        ]),
      ],
      targetGroups: [backendTg],
    });

    listener.addTargetGroups('MetricsUploads', {
      priority: 40,
      conditions: [
        elbv2.ListenerCondition.pathPatterns(['/metrics', '/uploads', '/uploads/*']),
      ],
      targetGroups: [backendTg],
    });

    // -------------------------------------------------------------------------
    // Auto Scaling (CPU target tracking)
    // -------------------------------------------------------------------------
    const backendScaling = this.backendService.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 6,
    });
    backendScaling.scaleOnCpuUtilization('BackendCpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.seconds(60),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });

    const frontendScaling = this.frontendService.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 4,
    });
    frontendScaling.scaleOnCpuUtilization('FrontendCpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.seconds(60),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });

    const workerScaling = this.workerService.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 4,
    });
    workerScaling.scaleOnCpuUtilization('WorkerCpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.seconds(120),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });

    // -------------------------------------------------------------------------
    // Outputs
    // -------------------------------------------------------------------------
    new cdk.CfnOutput(this, 'LoadBalancerDNS', {
      value: this.loadBalancer.loadBalancerDnsName,
      description: 'Application Load Balancer DNS name',
    });

    new cdk.CfnOutput(this, 'ApplicationURL', {
      value: `http://${this.loadBalancer.loadBalancerDnsName}`,
      description: 'Application base URL (HTTP)',
    });

    new cdk.CfnOutput(this, 'ClusterName', {
      value: this.cluster.clusterName,
      description: 'ECS cluster name',
    });

    new cdk.CfnOutput(this, 'BackendServiceName', {
      value: this.backendService.serviceName,
    });

    new cdk.CfnOutput(this, 'FrontendServiceName', {
      value: this.frontendService.serviceName,
    });

    new cdk.CfnOutput(this, 'WorkerServiceName', {
      value: this.workerService.serviceName,
    });

    new cdk.CfnOutput(this, 'BackendRepositoryUri', {
      value: backendRepo.repositoryUri,
      description: 'Push backend image here',
    });

    new cdk.CfnOutput(this, 'FrontendRepositoryUri', {
      value: frontendRepo.repositoryUri,
      description: 'Push frontend image here',
    });

    new cdk.CfnOutput(this, 'WorkerRepositoryUri', {
      value: workerRepo.repositoryUri,
      description: 'Push worker image here',
    });

    new cdk.CfnOutput(this, 'AppSecretArn', {
      value: appSecret.secretArn,
      description: 'Secrets Manager ARN for SECRET_KEY',
    });

    new cdk.CfnOutput(this, 'BackendSecurityGroupId', {
      value: backendSg.securityGroupId,
      description: 'Backend ECS security group ID',
    });

    new cdk.CfnOutput(this, 'WorkerSecurityGroupId', {
      value: workerSg.securityGroupId,
    });

    new cdk.CfnOutput(this, 'ImageTag', {
      value: imageTag,
      description: 'ECR image tag expected by task definitions',
    });
  }
}
