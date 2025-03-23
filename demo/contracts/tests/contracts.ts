import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Splitup } from "../target/types/splitup";
import { PublicKey, Keypair, SystemProgram } from "@solana/web3.js";
import { expect } from "chai";

describe("splitup", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.Splitup as Program<Splitup>;

  // Test accounts
  const user = Keypair.generate();
  const node = Keypair.generate();
  const model = Keypair.generate();
  const task = Keypair.generate();
  const execution = Keypair.generate();

  before(async () => {
    // Airdrop SOL to user for transactions
    const signature = await provider.connection.requestAirdrop(
      user.publicKey,
      2 * anchor.web3.LAMPORTS_PER_SOL
    );
    await provider.connection.confirmTransaction(signature);
  });

  describe("Task Registry", () => {
    it("should register a task successfully", async () => {
      const taskInfo = {
        id: new anchor.BN(1),
        model_id: new anchor.BN(1),
        description: "Test Description",
        vram_requirement: 16,
        compute_units: 1000,
        inputs: [
          {
            dtype: "float32",
            shape: [1, 28, 28],
            uri: "ipfs://input1",
          },
        ],
        outputs: [
          {
            dtype: "float32",
            shape: [1, 10],
            uri: "ipfs://output1",
          },
        ],
        weight_uri: "ipfs://weights1",
      };

      await program.methods
        .registerTask(taskInfo)
        .accounts({
          task: task.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, task])
        .rpc();

      const taskAccount = await program.account.task.fetch(task.publicKey);
      expect(taskAccount.initialized).to.be.true;
      expect(taskAccount.info.id.toString()).to.equal("1");
    });
  });

  describe("Model Registry", () => {
    it("should register a model successfully", async () => {
      // First register the tasks that will be used in the model
      const task1Info = {
        id: new anchor.BN(1),
        model_id: new anchor.BN(1),
        description: "Task 1",
        vram_requirement: 16,
        compute_units: 1000,
        inputs: [
          {
            dtype: "float32",
            shape: [1, 28, 28],
            uri: "ipfs://input1",
          },
        ],
        outputs: [
          {
            dtype: "float32",
            shape: [1, 10],
            uri: "ipfs://output1",
          },
        ],
        weight_uri: "ipfs://weights1",
      };

      const task2Info = {
        id: new anchor.BN(2),
        model_id: new anchor.BN(1),
        description: "Task 2",
        vram_requirement: 16,
        compute_units: 1000,
        inputs: [
          {
            dtype: "float32",
            shape: [1, 10],
            uri: "ipfs://input2",
          },
        ],
        outputs: [
          {
            dtype: "float32",
            shape: [1, 10],
            uri: "ipfs://output2",
          },
        ],
        weight_uri: "ipfs://weights2",
      };

      const task1 = Keypair.generate();
      const task2 = Keypair.generate();

      // Register task 1
      await program.methods
        .registerTask(task1Info)
        .accounts({
          task: task1.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, task1])
        .rpc();

      // Register task 2
      await program.methods
        .registerTask(task2Info)
        .accounts({
          task: task2.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, task2])
        .rpc();

      const modelInfo = {
        id: new anchor.BN(1),
        name: "Test Model",
        description: "Test Description",
        task_ids: [new anchor.BN(1), new anchor.BN(2)],
        creator: user.publicKey.toString(),
        connections: [
          {
            source_task_id: new anchor.BN(1),
            source_output_index: 0,
            destination_task_id: new anchor.BN(2),
            dest_input_index: 0,
            tensor_spec: {
              dtype: "float32",
              shape: [1, 28, 28],
              name: "input",
              dimensions: ["1", "28", "28"],
            },
          },
        ],
      };

      await program.methods
        .registerModel(modelInfo)
        .accounts({
          model: model.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .remainingAccounts([
          {
            pubkey: task1.publicKey,
            isWritable: false,
            isSigner: false,
          },
          {
            pubkey: task2.publicKey,
            isWritable: false,
            isSigner: false,
          },
        ])
        .signers([user, model])
        .rpc();

      const modelAccount = await program.account.model.fetch(model.publicKey);
      expect(modelAccount.initialized).to.be.true;
      expect(modelAccount.info.id.toString()).to.equal("1");
    });
  });

  describe("Node Registry", () => {
    it("should register a node successfully", async () => {
      const nodeInfo = {
        specializations: [
          {
            taskId: new anchor.BN(1),
            performance: new anchor.BN(100),
          },
        ],
        stakeAmount: new anchor.BN(1000),
      };

      await program.methods
        .registerNode(nodeInfo)
        .accounts({
          node: node.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, node])
        .rpc();

      const nodeAccount = await program.account.node.fetch(node.publicKey);
      expect(nodeAccount.initialized).to.be.true;
      expect(nodeAccount.owner.toString()).to.equal(user.publicKey.toString());
    });

    it("should stake collateral successfully", async () => {
      const stakeAmount = new anchor.BN(2000);

      await program.methods
        .stakeCollateral(stakeAmount)
        .accounts({
          node: node.publicKey,
          owner: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user])
        .rpc();

      const nodeAccount = await program.account.node.fetch(node.publicKey);
      expect(nodeAccount.info.stakeAmount.toString()).to.equal("3000"); // 1000 (initial) + 2000
    });
  });

  describe("Task Registry", () => {
    it("should register a task successfully", async () => {
      const taskInfo = {
        id: new anchor.BN(1),
        modelId: new anchor.BN(1),
        inputs: [
          {
            shape: [1, 28, 28],
            dtype: "float32",
            uri: "ipfs://input1",
          },
        ],
        outputs: [
          {
            shape: [1, 10],
            dtype: "float32",
            uri: "ipfs://output1",
          },
        ],
        weightUri: "ipfs://weights1",
        computeUnits: new anchor.BN(100),
      };

      await program.methods
        .registerTask(taskInfo)
        .accounts({
          task: task.publicKey,
          authority: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, task])
        .rpc();

      const taskAccount = await program.account.task.fetch(task.publicKey);
      expect(taskAccount.initialized).to.be.true;
      expect(taskAccount.info.id.toString()).to.equal("1");
    });
  });

  describe("Model Execution", () => {
    it("should request model execution successfully", async () => {
      const modelId = new anchor.BN(1);
      const inputUri = "ipfs://execution-input1";

      await program.methods
        .requestModelExecution(modelId, inputUri)
        .accounts({
          execution: execution.publicKey,
          user: user.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .signers([user, execution])
        .rpc();

      const executionAccount = await program.account.execution.fetch(
        execution.publicKey
      );
      expect(executionAccount.status.toString()).to.equal("Requested");
      expect(executionAccount.modelId.toString()).to.equal("1");
      expect(executionAccount.inputUri).to.equal(inputUri);
    });

    it("should complete a task successfully", async () => {
      const taskId = new anchor.BN(1);
      const outputUris = ["ipfs://task-output1"];

      await program.methods
        .completeTask(taskId, outputUris)
        .accounts({
          execution: execution.publicKey,
          node: node.publicKey,
        })
        .signers([node])
        .rpc();

      const executionAccount = await program.account.execution.fetch(
        execution.publicKey
      );
      expect(executionAccount.completedTasks).to.have.lengthOf(1);
      expect(executionAccount.completedTasks[0].taskId.toString()).to.equal(
        "1"
      );
      expect(executionAccount.completedTasks[0].outputUris[0]).to.equal(
        outputUris[0]
      );
    });

    it("should cancel execution successfully", async () => {
      await program.methods
        .cancelExecution()
        .accounts({
          execution: execution.publicKey,
          user: user.publicKey,
        })
        .signers([user])
        .rpc();

      const executionAccount = await program.account.execution.fetch(
        execution.publicKey
      );
      expect(executionAccount.status.toString()).to.equal("Canceled");
    });
  });
});
